WITH user_session_data AS (
    SELECT * FROM {{ ref("user_session_channel") }}
),
session_timestamp_data AS (
    SELECT * FROM {{ ref("session_timestamp") }}
)
SELECT 
    user_session_data.userId, 
    user_session_data.sessionId, 
    user_session_data.channel, 
    session_timestamp_data.ts
FROM user_session_data
JOIN session_timestamp_data ON user_session_data.sessionId = session_timestamp_data.sessionId
EOF
