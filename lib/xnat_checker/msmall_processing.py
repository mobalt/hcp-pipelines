#!/usr/bin/env python3

import sys
import argparse
from ccf.one_subject_completion_xnat_checker import MsmAllCompletionChecker

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Program to check for completion of MSM-All Processing."
    )

    # mandatory arguments
    parser.add_argument("-p", "--project", dest="project", required=True, type=str)
    parser.add_argument("-s", "--subject", dest="subject", required=True, type=str)
    parser.add_argument(
        "-c", "--classifier", dest="classifier", required=True, type=str
    )
    parser.add_argument(
        "-f",
        "--fieldmap",
        dest="fieldmap",
        required=False,
        type=str,
        default="SpinEcho",
    )
    # optional arguments
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        required=False,
        default=False,
    )
    parser.add_argument("-o", "--output", dest="output", required=False, type=str)
    parser.add_argument(
        "-a",
        "--check-all",
        dest="check_all",
        action="store_true",
        required=False,
        default=False,
    )
    parser.add_argument(
        "-m",
        "--marked",
        dest="marked",
        action="store_true",
        required=False,
        default=False,
    )
    # parse the command line arguments
    args = parser.parse_args()

    # check the specified subject for structural preprocessing completion
    completion_checker = MsmAllCompletionChecker(args.project, args.subject, args.classifier)

    if args.output:
        processing_output = open(args.output, "w")
    else:
        processing_output = sys.stdout

    if args.marked:
        if completion_checker.is_processing_marked_complete(
        ):
            print("Exiting with 0 code - Marked Completion Check Successful")
            exit(0)
        else:
            print("Exiting with 1 code - Marked Completion Check Unsuccessful")
            exit(1)
    else:
        if completion_checker.is_processing_complete(
            fieldmap=args.fieldmap,
            verbose=args.verbose,
            output=processing_output,
            short_circuit=not args.check_all,
        ):
            print("Exiting with 0 code - Completion Check Successful")
            exit(0)
        else:
            print("Exiting with 1 code - Completion Check Unsuccessful")
            exit(1)
