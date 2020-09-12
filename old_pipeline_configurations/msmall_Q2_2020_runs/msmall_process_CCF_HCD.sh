module load singularity-3.2.1

export XNAT_PBS_JOBS_CONTROL=${HOME}/processing/msmall_Q2_2020_runs/xnat_pbs_jobs_control_CCF_HCD

singularity exec -B /NRG-data/NRG/intradb/archive,/NRG-data/NRG/intradb/build_ssd,/usr/local/torque-6.1.2,/export/HCP/qunex-hcp \
/export/HCP/qunex-hcp/production_containers/Process/HCPpipelines_XNAT_1_0_5.sif \
/pipeline_tools/xnat_pbs_jobs/MsmAllProcessing/SubmitMsmAllProcessingBatch intradb $1
