WITH src_user_session_channel AS (
    SELECT * 
    FROM {{ source('raw', 'user_session_channel') }}
)
SELECT
    userId,
    sessionId,
    channel
FROM src_user_session_channel
WHERE sessionId IS NOT NULL