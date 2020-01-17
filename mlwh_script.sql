SELECT
    id_run, position, qc_seq
FROM
    iseq_run_lane_metrics
WHERE
    flowcell_barcode IN (SELECT DISTINCT
            (flowcell_barcode)
        FROM
            iseq_flowcell
        WHERE
            id_flowcell_lims = __BATCH_ID__) and position = __POSITION__;
