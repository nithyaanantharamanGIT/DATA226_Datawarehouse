WITH src_session_timestamp AS (
    SELECT * 
    FROM {{ source('raw', 'session_timestamp') }}
)
SELECT
    sessionId,
    ts
FROM src_session_timestamp
WHERE sessionId IS NOT NULL