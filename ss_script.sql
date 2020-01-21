SELECT
    requests.target_asset_id AS target_asset_id,
    batch_requests.position AS position,
    batch_requests.batch_id AS batch_id
FROM
    batch_requests
        INNER JOIN
    requests ON requests.id = batch_requests.request_id
        INNER JOIN
    events ON events.eventful_id = batch_requests.request_id
WHERE
    requests.initial_study_id = 5902
        AND requests.state = 'started'
        AND requests.request_type_id = 168
        AND events.message LIKE '%qc complete%'
ORDER BY batch_requests.batch_id , batch_requests.position ASC
limit 1;
