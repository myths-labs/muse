#!/usr/bin/env python3
"""Probe the selected Python under isolation; optionally verify PNG/JPEG decoding."""
import argparse
import json
import os
import subprocess
import sys

# Fixed 1x1 RGB images, generated once and decoded as independent format fixtures.
FIXTURES = {
    "PNG": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPgUbIAAACkAGeY0OCYAAAAAElFTkSuQmCC",
    "JPEG": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDx2iiiu04z/9k="
}
CHILD = r'''
import base64
import io
import json
import site
import sys

report = {
    "status": "PASS", "error": None,
    "runtime": {
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "isolated": sys.flags.isolated,
        "ignore_environment": sys.flags.ignore_environment,
        "user_site_enabled": site.ENABLE_USER_SITE,
    },
    "image_decoder": {"required": sys.argv[1] == "1", "status": "NOT_REQUESTED", "formats": []},
}

def finish(error=None):
    if error:
        report["status"] = "FAIL"
        report["error"] = error
    print(json.dumps(report, sort_keys=True))
    sys.exit(2 if error else 0)

if sys.version_info < (3, 7):
    finish("PYTHON_VERSION_UNSUPPORTED")
if sys.flags.isolated != 1 or sys.flags.ignore_environment != 1 or site.ENABLE_USER_SITE is not False:
    finish("PYTHON_ISOLATION_UNAVAILABLE")
if report["image_decoder"]["required"]:
    report["image_decoder"]["status"] = "FAIL"
    try:
        import PIL
        from PIL import Image
    except Exception as exc:
        report["image_decoder"]["error_type"] = type(exc).__name__
        finish("IMAGE_DECODER_UNAVAILABLE")
    report["image_decoder"]["pillow_version"] = getattr(PIL, "__version__", None)
    report["image_decoder"]["module_path"] = getattr(PIL, "__file__", None)
    fixtures = json.loads(sys.argv[2])
    for name in ("PNG", "JPEG"):
        try:
            raw = base64.b64decode(fixtures[name], validate=True)
            with Image.open(io.BytesIO(raw)) as image:
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
                if image.format != name or image.size != (1, 1):
                    raise ValueError("Unexpected image fixture")
        except Exception as exc:
            report["image_decoder"]["error_type"] = type(exc).__name__
            report["image_decoder"]["failed_format"] = name
            finish("IMAGE_DECODER_FAILED")
        report["image_decoder"]["formats"].append(name)
    report["image_decoder"]["status"] = "PASS"
finish()
'''


def probe(python, require_image_decoder, timeout=15):
    report = {
        "schema_version": 1, "status": "FAIL", "error": None,
        "requested_python": python, "child_flags": ["-I", "-B"],
        "runtime": None,
        "image_decoder": {"required": require_image_decoder, "status": "NOT_CHECKED", "formats": []},
    }

    def fail(code):
        report["error"] = code
        return report

    if not isinstance(python, str) or not os.path.isabs(python):
        return fail("PYTHON_PATH_MUST_BE_ABSOLUTE")
    # Do not realpath/resolve: a virtualenv launcher can be a symlink to base Python.
    command = [python, "-I", "-B", "-c", CHILD, "1" if require_image_decoder else "0", json.dumps(FIXTURES)]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return fail("PYTHON_PROBE_TIMEOUT")
    except OSError:
        return fail("PYTHON_EXECUTABLE_UNAVAILABLE")
    except UnicodeError:
        return fail("PYTHON_PROBE_INVALID_RESPONSE")
    if len(result.stdout) > 65536 or len(result.stderr) > 65536:
        return fail("PYTHON_PROBE_OUTPUT_LIMIT")
    try:
        child = json.loads(result.stdout)
        if not isinstance(child, dict) or child.get("status") not in ("PASS", "FAIL"):
            raise ValueError("Invalid status")
        if result.returncode != (0 if child["status"] == "PASS" else 2) or result.stderr:
            raise ValueError("Unexpected subprocess result")
        runtime = child["runtime"]
        if runtime["isolated"] != 1 or runtime["ignore_environment"] != 1 or runtime["user_site_enabled"] is not False:
            return fail("PYTHON_ISOLATION_UNAVAILABLE")
        if child["status"] == "PASS" and require_image_decoder:
            if child["image_decoder"]["status"] != "PASS" or child["image_decoder"]["formats"] != ["PNG", "JPEG"]:
                raise ValueError("Image checks incomplete")
        report.update({key: child[key] for key in ("status", "error", "runtime", "image_decoder")})
    except (KeyError, TypeError, ValueError):
        return fail("PYTHON_PROBE_INVALID_RESPONSE")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable, help="Absolute interpreter path; preserve the virtualenv launcher.")
    parser.add_argument("--require-image-decoder", action="store_true", help="Require Pillow plus PNG/JPEG verify and load under -I.")
    args = parser.parse_args()
    report = probe(args.python, args.require_image_decoder)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
