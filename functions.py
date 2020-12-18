import glob
import os
import random
import shutil
import time
from .util import escape_path, keep_resting_state_scans, shell_run, qsub, is_unreadable


def check_required_files_are_available(
    QUNEX_CONTAINER,
    PIPELINES_CONTAINER,
    XNAT_CREDENTIALS_FILE,
    EXPECTED_FILES_LIST,
    QUNEX_PARAMETER_FILES,
    GRADIENT_COEFFICIENT_PATH,
    HCP_LIB_DIR,
    FREESURFER_LICENSE_PATH,
):
    if is_unreadable(QUNEX_CONTAINER):
        raise Exception("QUNEX_CONTAINER is not accessible. Value = ", QUNEX_CONTAINER)
    if is_unreadable(PIPELINES_CONTAINER):
        raise Exception("PIPELINES_CONTAINER is not accessible. Value = ", PIPELINES_CONTAINER)
    if is_unreadable(XNAT_CREDENTIALS_FILE):
        raise Exception("XNAT_CREDENTIALS_FILE is not accessible. Value = ", XNAT_CREDENTIALS_FILE)
    if is_unreadable(EXPECTED_FILES_LIST):
        raise Exception("EXPECTED_FILES_LIST is not accessible. Value = ", EXPECTED_FILES_LIST)
    if is_unreadable(QUNEX_PARAMETER_FILES):
        raise Exception("QUNEX_PARAMETER_FILES is not accessible. Value = ", QUNEX_PARAMETER_FILES)
    #MRH:  Not sure why the path is showing up as unreadable by os.access, but let's not check it
    #if is_unreadable(GRADIENT_COEFFICIENT_PATH):
    #    raise Exception("GRADIENT_COEFFICIENT_PATH is not accessible. Value = ", GRADIENT_COEFFICIENT_PATH)
    if is_unreadable(HCP_LIB_DIR):
        raise Exception("HCP_LIB_DIR is not accessible. Value = ", HCP_LIB_DIR)
    if is_unreadable(FREESURFER_LICENSE_PATH):
        raise Exception("FREESURFER_LICENSE_PATH is not accessible. Value = ", FREESURFER_LICENSE_PATH)


def generate_timestamp(TIMESTAMP=None):
    if TIMESTAMP is None:
        return {"TIMESTAMP": str(int(time.time()))}


def split_subject_components(SUBJECT_ARG):
    components = SUBJECT_ARG.split(":")
    if len(components) != 4:
        raise ValueError(
            "Expecting a colon-delimited SUBJECT_ARG in the format AA:BB:CC:DD, instead got: ",
            SUBJECT_ARG,
        )

    proj, subject_id, classifier, scan = components

    if scan == "all":
        scan = ""
    _scan = "_" + scan if scan else ""

    return {
        "PROJECT": proj,
        "SUBJECT": subject_id,
        "CLASSIFIER": classifier,
        "SCAN": scan,
        "_SCAN": _scan,
        "SESSION": f"{subject_id}_{classifier}",
    }


def get_project_acronym(PROJECT):
    proj = PROJECT
    if "HCA" in proj:
        proj_acronym = "HCA"
    elif "HCD" in proj:
        proj_acronym = "HCD"
    elif "MDD" in proj:
        proj_acronym = "MDD"
    elif "BWH" in proj:
        proj_acronym = "BWH"
    else:
        raise ValueError(
            "Unexpected project value. Expecting HCA, HCD, MDD, or BWH. Got: ", proj
        )
    return {
        "PROJECT_ACRONYM": proj_acronym,
    }


def choose_put_server(PUT_SERVER_LIST, PUT_SERVER=None):
    if PUT_SERVER is not None:
        print("PUT_SERVER has already been set. Skipping regeneration.")
        return

    server_list = PUT_SERVER_LIST.split(" ")
    chosen = random.choice(server_list)

    return {
        "PUT_SERVER": chosen,
    }


def set_study_folder(
    WORKING_DIR,
    SESSION,
    SCRATCH_SPACE,
    WORKING_DIR_BASENAME,
    USE_SCRATCH_FOR_PROCESSING,
):
    if USE_SCRATCH_FOR_PROCESSING:
        WORKING_DIR_SCRATCH = f"{SCRATCH_SPACE}/{WORKING_DIR_BASENAME}"
    else:
        WORKING_DIR_SCRATCH = WORKING_DIR
    STUDY_FOLDER_SCRATCH = os.path.join(WORKING_DIR_SCRATCH, SESSION)
    STUDY_FOLDER = os.path.join(WORKING_DIR, SESSION)
    STUDY_FOLDER_REPL = escape_path(STUDY_FOLDER)

    return {
        "STUDY_FOLDER": STUDY_FOLDER,
        "STUDY_FOLDER_SCRATCH": STUDY_FOLDER_SCRATCH,
        "STUDY_FOLDER_REPL": STUDY_FOLDER_REPL,
        "WORKING_DIR_SCRATCH": WORKING_DIR_SCRATCH,
    }


def make_directories(
    DRYRUN, WORKING_DIR, STUDY_FOLDER, CHECK_DATA_DIR, MARK_COMPLETION_DIR
):
    if not DRYRUN:
        print("Making ", WORKING_DIR)
        os.makedirs(WORKING_DIR, exist_ok=True)
        print("Making study folder: ", WORKING_DIR)
        os.makedirs(f"{STUDY_FOLDER}/processing", exist_ok=True)
        print("Making ", CHECK_DATA_DIR)
        os.makedirs(CHECK_DATA_DIR, exist_ok=True)
        #print("Making ", MARK_COMPLETION_DIR)
        #os.makedirs(MARK_COMPLETION_DIR, exist_ok=True)


# def copy_free_surfer_assessor_script(
#     DRYRUN, XNAT_PBS_JOBS, PIPELINE_NAME, WORKING_DIR, PRUNNER_CONFIG_DIR
# ):
#     source = f"{XNAT_PBS_JOBS}/{PIPELINE_NAME}/{PIPELINE_NAME}.XNAT_CREATE_FREESURFER_ASSESSOR"
#     dest = f"{WORKING_DIR}/{PIPELINE_NAME}.XNAT_CREATE_FREESURFER_ASSESSOR"
#     if not DRYRUN:
#         shutil.copy(source, dest)
#         os.chmod(dest, 0o770)
#
#     return {"FREESURFER_ASSESSOR_DEST_PATH": dest}


def launch_main_script(SUBMIT_TO_PBS_SCRIPT, DRYRUN, AUTOLAUNCH_AT_END):
    if DRYRUN:
        print(
            "Dry-Mode is active: Skipping the launch of the main script to prevent side-effects."
        )
    elif not AUTOLAUNCH_AT_END:
        print(
            "AUTOLAUNCH_AT_END has been set to False. Change that in common_vars section of variables.yaml to autolaunch."
        )
    else:
        print("Launching main Bash script...")
        shell_run(SUBMIT_TO_PBS_SCRIPT)


def available_bold_dirs(ARCHIVE_ROOT, SESSION, PROJECT):
    """
    List of full paths to any resource containing preprocessed functional data
    for the specified subject
    """

    archive_root = f"{ARCHIVE_ROOT}/{PROJECT}/arc001"
    functional_preproc_dir = f"{archive_root}/{SESSION}/RESOURCES/*fMRI*preproc"
    dir_list = sorted(glob.glob(functional_preproc_dir))
    available_bolds = [d[d.rindex("/") + 1 : d.index("_preproc")] for d in dir_list]

    def fmrisort(x):
        priority = [
            "rfMRI_REST1_AP",
            "rfMRI_REST1_PA",
            "rfMRI_REST1a_PA",
            "rfMRI_REST1a_AP",
            "rfMRI_REST1b_PA",
            "rfMRI_REST1b_AP",
            "tfMRI_GUESSING_PA",
            "tfMRI_GUESSING_AP",
            "tfMRI_VISMOTOR_PA",
            "tfMRI_CARIT_PA",
            "tfMRI_CARIT_AP",
            "tfMRI_EMOTION_PA",
            "tfMRI_FACENAME_PA",
            "rfMRI_REST2_AP",
            "rfMRI_REST2_PA",
            "rfMRI_REST2a_AP",
            "rfMRI_REST2a_PA",
            "rfMRI_REST2b_AP",
            "rfMRI_REST2b_PA",
        ]
        return priority.index(x)

    available_bolds = sorted(available_bolds, key=fmrisort)
    return {"BOLD_LIST": available_bolds}


def set_msm_all_bolds(BOLD_LIST):
    resting_bolds = keep_resting_state_scans(BOLD_LIST)
    MSM_ALL_BOLDS = ",".join(resting_bolds)

    return {"MSM_ALL_BOLDS": MSM_ALL_BOLDS}


def set_bold_list_order(PROJECT, SCAN):
    # possible values for BOLD_LIST_ORDER
    BLO_HCA = "hca"
    BLO_HCD_YOUNG = "hcd_5_to_7"
    BLO_HCD_OLDER = "hcd_8_and_up"

    if PROJECT == "CCF_HCA_STG" or "CCF_HCA_TST":
        bold_list_order = BLO_HCA
    else:
        if SCAN == "YOUNGER":
            bold_list_order = BLO_HCD_YOUNG
        elif SCAN == "OLDER":
            bold_list_order = BLO_HCD_OLDER
        else:
            raise ValueError("The subject subgroup should be YOUNGER or OLDER.")

    return {"BOLD_LIST_ORDER": bold_list_order}


def set_qunex_scanlist(BOLD_LIST_ORDER, BOLD_LIST):
    qunex_scanlist = [scan for scan in BOLD_LIST_ORDER if scan[1] in BOLD_LIST]
    return {"QUNEX_SCANLIST": qunex_scanlist}


def set_qunex_scanlist_dwi(PROJECT, SCAN):
    if PROJECT in ["CCF_HCA_STG", "CCF_HCD_STG", "CCF_HCA_TST", "CCF_HCD_TST"]:
        qunex_scanlist = [
            ['01: DWI:dir98_AP','dMRI_dir98_AP'],
            ['02: DWI:dir98_PA','dMRI_dir98_PA'],
            ['03: DWI:dir99_AP','dMRI_dir99_AP'],
            ['04: DWI:dir99_PA','dMRI_dir99_PA']
        ]
    return {"QUNEX_SCANLIST": qunex_scanlist}
