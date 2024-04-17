load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("@pip//:requirements.bzl", "requirement")
load("@rules_python//python:py_binary.bzl", "py_binary")

package(default_visibility = ["//visibility:public"])

# NB: Regenerate `requirements.txt` with:
#
#   bazel run :requirements.update
#
compile_pip_requirements(
    name = "requirements",
    src = "requirements.in",
    requirements_txt = "requirements.txt",
    visibility = ["//visibility:public"],
)

py_library(
    name = "params",
    srcs = ["params.py"],
)

py_binary(
    name = "generate",
    srcs = ["generate.py"],
    data = [":requirements"],
    deps = [":params"],
)

sh_binary(
    name = "run",
    srcs = ["run.sh"],
    data = [
        ":generate",
    ],
)
