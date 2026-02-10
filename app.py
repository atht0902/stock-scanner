SELECT 
    A.user_id,
    A.event_name,
    A.event_timestamp,
    B.metadata_value
FROM 
    events_table AS A
LEFT JOIN 
    metadata_table AS B ON A.event_id = B.event_id
WHERE 
    A.event_timestamp >= '2024-01-01'
    AND A.status = 'ACTIVE'
LIMIT 100;
