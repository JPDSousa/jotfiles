#  MIT License
#
#  Copyright (c) 2021 João Sousa
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

# coding=utf-8

import logging
import os
import re
import sys
from dataclasses import dataclass
from subprocess import Popen
from typing import List, Optional

from jotfiles.bash import run_bash

logger = logging.getLogger(__name__)


@dataclass
class MavenRepo:
    path: str
    port: str


home_dir: str = os.getenv("HOME")
default_repo: MavenRepo = MavenRepo(home_dir + "/.m2", "8000")
progress_re = re.compile(r".*\[(\d+)/(\d+)]")


def _local_repo() -> str:
    repo_path = default_repo.path
    logger.debug("Installing to local repo: %s", repo_path)
    return "-Dmaven.repo.local=" + repo_path + "/repository"


def _port(override: Optional[str] = None) -> str:
    repo_port = default_repo.port
    logger.debug("Using debug port: %s", repo_port)
    return "address=" + (override if override is not None else repo_port)


def _debug(suspend: bool = False, port: Optional[str] = None) -> str:
    prop = "-Dmaven.surefire.debug="
    sus_flag = "suspend=" + ("y" if suspend else "n")
    address = _port(port)
    return (
        prop + '"-Xdebug -Xrunjdwp:transport=dt_socket,server=y,{},{} '
        '-Xnoagent -Djava.compiler=NONE"'.format(sus_flag, address)
    )


def compile_mvn(clean: bool, extra_args: List[str]) -> None:
    logger.info("Compiling maven project")
    mvn_args = ["install", "-DskipTests", *extra_args]
    if clean:
        logger.debug("Prepending clean lifecycle")
        mvn_args = ["clean", *mvn_args]
    ps = mvn(*mvn_args)
    summary = False
    biggest_line = 0
    for line in ps.stdout:
        line = line.decode("UTF-8")
        match = progress_re.match(line)
        summary = (
            summary
            or line.startswith("[INFO] Reactor Summary:")
            or line.startswith("[INFO] BUILD")
        )
        error = line.startswith("[ERROR]")
        if summary or error:
            print(line.rstrip("\n"))
        elif match:
            current = int(match.group(1))
            total = int(match.group(2))
            remaining = total - current
            current_ticks = max(int(current * 100 / total), 1)
            remaining_ticks = max(int(remaining * 100 / total), 1)
            progress = "[%s%s] %d/%d " % (
                "#" * current_ticks,
                " " * remaining_ticks,
                current,
                total,
            )
            biggest_line = max(len(progress), biggest_line)
            print(progress, end="\r")
            sys.stdout.flush()
    ps.wait()
    # clear line
    print(" " * biggest_line, end="\r")
    logger.info("Maven project compiled")


def test(
    module: str,
    test_reference: str,
    comp: bool = True,
    suspend: bool = False,
    port: Optional[str] = None,
    cmd: bool = False,
) -> Optional[str]:
    return _test(module, test_reference, comp=comp, suspend=suspend, port=port, cmd=cmd)


def _test(
    module: str,
    test_reference: str,
    profiles: Optional[List[str]] = None,
    comp: bool = True,
    suspend: bool = False,
    port: Optional[str] = None,
    cmd: bool = False,
    *args,
) -> Optional[str]:
    if profiles is None:
        profiles = []
    profiles = ["-P" + profile for profile in profiles if profile]
    phase = "test" if comp else "surefire:test"
    pl = "" if module is None else "-pl :" + module
    test_arg = "-Dtest=" + test_reference
    # debug is only active if suspend
    debug = _debug(suspend, port) if suspend else ""
    logger.info("Test starting")
    # this is the maven command
    cmd_str = mvn_cmd(phase, pl, test_arg, *profiles, "-o", debug, *args)
    if cmd:
        logger.info("Maven command: %s", cmd_str)
        return cmd_str
    ps = run_bash(cmd_str)
    for line in ps.stdout:
        print(line.decode("UTF-8"), end="")
    ps.wait()
    logger.info("Tests finished.")


def mvn_cmd(*args) -> str:
    base_args = ["-fae", "-nsu", "-T 1.5C", "-Dstyle.color=always"]
    local_repo = _local_repo()
    return " ".join(["mvn", *args, *base_args, local_repo])


def mvn(*args) -> Popen:
    return run_bash(mvn_cmd(*args))
