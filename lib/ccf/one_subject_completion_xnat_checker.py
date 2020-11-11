#!/usr/bin/env python3

"""
Abstract Base Class for One Subject Completion Checker Classes
"""
import abc
import os
import sys
from utils import os_utils, file_utils
import ccf.archive as ccf_archive

hcp_run_utils = os_utils.getenv_required("HCP_RUN_UTILS")
xnat_pbs_jobs = os_utils.getenv_required("XNAT_PBS_JOBS")


def expected_output_files_template_filename(fieldmap):
    """Name of the file containing a list of templates for expected output files"""
    return f"ExpectedOutputFiles-FieldMap-{fieldmap}.CCF.txt"


class OneSubjectCompletionXnatChecker(abc.ABC):
    """
    Abstract base class for classes that are used to check the completion
    of pipeline processing for one subject
    """

    def __init__(self, project, subject, classifier, scan):
        self.SUBJECT_PROJECT = project
        self.SUBJECT_ID = subject
        self.SUBJECT_CLASSIFIER = classifier
        self.SUBJECT_EXTRA = scan
        self.SUBJECT_SESSION = f"{classifier}_{scan}"
        self.archive = ccf_archive.CcfArchive(project, subject, classifier, scan)

    @property
    def processing_name(self):
        """Name of processing type to check (e.g. StructuralPreprocessing, FunctionalPreprocessing, etc.)"""
        raise NotImplementedError

    def list_of_expected_files(self, working_dir, fieldmap):

        if os.path.isfile(
            hcp_run_utils
            + "/"
            + self.processing_name
            + "/"
            + expected_output_files_template_filename(fieldmap)
        ):
            f = open(
                hcp_run_utils
                + "/"
                + self.processing_name
                + "/"
                + expected_output_files_template_filename(fieldmap)
            )
        else:
            f = open(
                xnat_pbs_jobs
                + "/"
                + self.processing_name
                + "/"
                + expected_output_files_template_filename(fieldmap)
            )

        root_dir = "/".join([working_dir, self.SUBJECT_SESSION])
        l = file_utils.build_filename_list_from_file(
            f,
            root_dir,
            subjectid=self.SUBJECT_SESSION,
            scan=self.SUBJECT_EXTRA,
        )
        return l

    def do_all_files_exist(
        self, file_name_list, verbose=False, output=sys.stdout, short_circuit=True
    ):
        return file_utils.do_all_files_exist(
            file_name_list, verbose, output, short_circuit
        )

    def my_prerequisite_dir_full_paths(self):
        raise NotImplementedError

    def my_resource(self):
        raise NotImplementedError

    def my_resource_time_stamp(self):
        return os.path.getmtime(self.my_resource())

    def does_processed_resource_exist(self):
        fullpath = self.my_resource()
        return os.path.isdir(fullpath)

    def latest_prereq_resource_time_stamp(self):
        latest_time_stamp = 0
        prerequisite_dir_paths = self.my_prerequisite_dir_full_paths()

        for full_path in prerequisite_dir_paths:
            this_time_stamp = os.path.getmtime(full_path)
            if this_time_stamp > latest_time_stamp:
                latest_time_stamp = this_time_stamp

        return latest_time_stamp

    def is_processing_marked_complete(self):
        # If the processed resource does not exist, then the process is certainly not marked
        # as complete. The file that marks completeness would be in that resource.
        if not self.does_processed_resource_exist():
            return False

        resource_path = (
            self.my_resource()
            + "/"
            + self.SUBJECT_ID
            + "_"
            + self.SUBJECT_CLASSIFIER
            + "/"
            + "ProcessingInfo"
        )

        subject_pipeline_name = self.SUBJECT_SESSION
        subject_pipeline_name_check = self.SUBJECT_ID + "." + self.SUBJECT_CLASSIFIER
        if self.SUBJECT_EXTRA.lower() != "all" and self.SUBJECT_EXTRA != "":
            subject_pipeline_name += "_" + self.SUBJECT_EXTRA
            subject_pipeline_name_check += "." + self.SUBJECT_EXTRA
        subject_pipeline_name += "." + self.processing_name
        subject_pipeline_name_check += "." + self.processing_name

        completion_marker_file_path = (
            resource_path + "/" + subject_pipeline_name_check + ".XNAT_CHECK.success"
        )
        starttime_marker_file_path = (
            resource_path + "/" + subject_pipeline_name + ".starttime"
        )

        # If the completion marker file does not exist, the the processing is certainly not marked
        # as complete.
        marker_file_exists = os.path.exists(completion_marker_file_path)
        if not marker_file_exists:
            return False

        # If the completion marker file is older than the starttime marker file, then any mark
        # of completeness is invalid.
        if not os.path.exists(starttime_marker_file_path):
            return False

        if os.path.getmtime(completion_marker_file_path) < os.path.getmtime(
            starttime_marker_file_path
        ):
            return False

        # If the completion marker file does exist, then look at the contents for further
        # confirmation.

        f = open(completion_marker_file_path, "r")
        lines = f.readlines()

        if lines[-1].strip() != "Completion Check was successful":
            return False

        return True

    def is_processing_complete(
        self,
        fieldmap,
        verbose=False,
        output=sys.stdout,
        short_circuit=True,
    ):

        # If the processed resource does not exist, then the processing is certainly not complete.
        if not self.does_processed_resource_exist():
            if verbose:
                print(
                    "resource: " + self.my_resource() + " DOES NOT EXIST",
                    file=output,
                )
            return False

        # If processed resource is not newer than prerequisite resources, then the processing
        # is not complete.
        resource_time_stamp = self.my_resource_time_stamp()
        latest_prereq_time_stamp = self.latest_prereq_resource_time_stamp()

        if resource_time_stamp <= latest_prereq_time_stamp:
            if verbose:
                print(
                    "resource: "
                    + self.my_resource()
                    + " IS NOT NEWER THAN ALL PREREQUISITES",
                    file=output,
                )
            return False

        resource_file_path = self.my_resource()
        # If processed resource exists and is newer than all the prerequisite resources, then check
        # to see if all the expected files exist
        expected_file_list = self.list_of_expected_files(resource_file_path, fieldmap)
        return self.do_all_files_exist(
            expected_file_list, verbose, output, short_circuit
        )


class StructuralCompletionChecker(OneSubjectCompletionXnatChecker):
    @property
    def processing_name(self):
        return "StructuralPreprocessing"

    def my_resource(self):
        return self.archive.structural_preproc_dir_full_path()

    def my_prerequisite_dir_full_paths(self):
        return self.archive.available_structural_unproc_dir_full_paths()


class StructuralHandEditCompletionChecker(OneSubjectCompletionXnatChecker):
    @property
    def processing_name(self):
        return "StructuralPreprocessingHandEdit"

    def my_resource(self):
        return self.archive.structural_preproc_hand_edit_dir_full_path()

    def my_prerequisite_dir_full_paths(self):
        return self.archive.available_structural_preproc_dir_full_paths()


class FunctionalCompletionChecker(OneSubjectCompletionXnatChecker):
    @property
    def processing_name(self):
        return "FunctionalPreprocessing"

    def my_resource(self):
        return self.archive.functional_preproc_dir_full_path()

    def my_prerequisite_dir_full_paths(self):
        return [self.archive.structural_preproc_dir_full_path()]


class MultirunicafixCompletionChecker(OneSubjectCompletionXnatChecker):
    @property
    def processing_name(self):
        return "MultiRunIcaFixProcessing"

    def my_resource(self):
        return self.archive.multirun_icafix_dir_full_path()

    def my_prerequisite_dir_full_paths(self):
        return [self.archive.structural_preproc_dir_full_path()]


class MsmAllCompletionChecker(OneSubjectCompletionXnatChecker):
    @property
    def processing_name(self):
        return "MsmAllProcessing"

    def my_resource(self):
        return self.archive.msm_all_dir_full_path()

    def my_prerequisite_dir_full_paths(self):
        return [self.archive.structural_preproc_dir_full_path()]


class DiffusionCompletionChecker(OneSubjectCompletionXnatChecker):
    @property
    def processing_name(self):
        return "DiffusionPreprocessing"

    def my_resource(self):
        return self.archive.diffusion_preproc_dir_full_path()

    def my_prerequisite_dir_full_paths(self):
        return [self.archive.structural_preproc_dir_full_path()]
