-- =====================================================
-- FEEDBACK TABLE MIGRATION
-- =====================================================
-- This migration adds the feedback table to store beta user survey responses
-- Run this script to add feedback functionality to the LawVriksh platform

-- Create feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- User identification (optional - can be anonymous)
    user_id INT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,

    -- Contact information
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,

    -- Multiple choice responses
    biggest_hurdle ENUM('A', 'B', 'C', 'D', 'E') NOT NULL,
    biggest_hurdle_other TEXT NULL,
    primary_motivation ENUM('A', 'B', 'C', 'D') NULL,
    time_consuming_part ENUM('A', 'B', 'C', 'D') NULL,
    professional_fear ENUM('A', 'B', 'C', 'D') NOT NULL,

    -- Short answer responses (2-4 sentences each)
    monetization_considerations TEXT NULL,
    professional_legacy TEXT NULL,
    platform_impact TEXT NOT NULL,
    
    -- Metadata
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_feedback_user_id (user_id),
    INDEX idx_feedback_email (email),
    INDEX idx_feedback_submitted_at (submitted_at),
    INDEX idx_feedback_biggest_hurdle (biggest_hurdle),
    INDEX idx_feedback_primary_motivation (primary_motivation),
    INDEX idx_feedback_professional_fear (professional_fear),
    INDEX idx_feedback_time_consuming_part (time_consuming_part),
    
    -- Foreign key constraint (optional, allows anonymous feedback)
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Add comments for documentation
ALTER TABLE feedback COMMENT = 'Beta user feedback survey responses';

-- Column comments for clarity
ALTER TABLE feedback 
MODIFY COLUMN biggest_hurdle ENUM('A', 'B', 'C', 'D', 'E') NOT NULL 
COMMENT 'A=Time commitment, B=Simplifying topics, C=Audience reach, D=Ethics/compliance, E=Other',

MODIFY COLUMN biggest_hurdle_other TEXT NULL 
COMMENT 'Explanation when biggest_hurdle is E (Other)',

MODIFY COLUMN primary_motivation ENUM('A', 'B', 'C', 'D') NOT NULL 
COMMENT 'A=Brand building, B=Client attraction, C=Revenue stream, D=Education/contribution',

MODIFY COLUMN time_consuming_part ENUM('A', 'B', 'C', 'D') NOT NULL 
COMMENT 'A=Research, B=Drafting, C=Editing, D=Formatting',

MODIFY COLUMN professional_fear ENUM('A', 'B', 'C', 'D') NOT NULL 
COMMENT 'A=Losing clients, B=Becoming irrelevant, C=Being outdated, D=No fear',

MODIFY COLUMN monetization_considerations TEXT NOT NULL
COMMENT 'Practical/ethical considerations about monetizing expertise',

MODIFY COLUMN professional_legacy TEXT NOT NULL
COMMENT 'Definition of professional legacy and role of knowledge sharing',

MODIFY COLUMN platform_impact TEXT NOT NULL
COMMENT 'How an effortless platform would change career growth in 5 years',

MODIFY COLUMN ip_address VARCHAR(45) NULL 
COMMENT 'IP address for analytics and duplicate prevention',

MODIFY COLUMN user_agent TEXT NULL 
COMMENT 'Browser/device information for analytics';

-- Create view for feedback analytics
CREATE OR REPLACE VIEW feedback_analytics AS
SELECT 
    COUNT(*) as total_responses,
    
    -- Biggest hurdle breakdown
    SUM(CASE WHEN biggest_hurdle = 'A' THEN 1 ELSE 0 END) as hurdle_time_commitment,
    SUM(CASE WHEN biggest_hurdle = 'B' THEN 1 ELSE 0 END) as hurdle_simplifying,
    SUM(CASE WHEN biggest_hurdle = 'C' THEN 1 ELSE 0 END) as hurdle_audience_reach,
    SUM(CASE WHEN biggest_hurdle = 'D' THEN 1 ELSE 0 END) as hurdle_ethics,
    SUM(CASE WHEN biggest_hurdle = 'E' THEN 1 ELSE 0 END) as hurdle_other,
    
    -- Primary motivation breakdown
    SUM(CASE WHEN primary_motivation = 'A' THEN 1 ELSE 0 END) as motivation_brand,
    SUM(CASE WHEN primary_motivation = 'B' THEN 1 ELSE 0 END) as motivation_clients,
    SUM(CASE WHEN primary_motivation = 'C' THEN 1 ELSE 0 END) as motivation_revenue,
    SUM(CASE WHEN primary_motivation = 'D' THEN 1 ELSE 0 END) as motivation_education,
    
    -- Time consuming part breakdown
    SUM(CASE WHEN time_consuming_part = 'A' THEN 1 ELSE 0 END) as time_research,
    SUM(CASE WHEN time_consuming_part = 'B' THEN 1 ELSE 0 END) as time_drafting,
    SUM(CASE WHEN time_consuming_part = 'C' THEN 1 ELSE 0 END) as time_editing,
    SUM(CASE WHEN time_consuming_part = 'D' THEN 1 ELSE 0 END) as time_formatting,
    
    -- Professional fear breakdown
    SUM(CASE WHEN professional_fear = 'A' THEN 1 ELSE 0 END) as fear_losing_clients,
    SUM(CASE WHEN professional_fear = 'B' THEN 1 ELSE 0 END) as fear_irrelevant,
    SUM(CASE WHEN professional_fear = 'C' THEN 1 ELSE 0 END) as fear_outdated,
    SUM(CASE WHEN professional_fear = 'D' THEN 1 ELSE 0 END) as fear_none,
    
    -- Recent activity
    SUM(CASE WHEN submitted_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as responses_last_7_days,
    SUM(CASE WHEN submitted_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as responses_last_30_days,
    
    -- Date range
    MIN(submitted_at) as first_response,
    MAX(submitted_at) as latest_response
    
FROM feedback;

-- Create view for detailed feedback with user info
CREATE OR REPLACE VIEW feedback_with_user AS
SELECT 
    f.*,
    u.name as user_name,
    u.email as user_email,
    u.is_admin as user_is_admin,
    u.created_at as user_created_at
FROM feedback f
LEFT JOIN users u ON f.user_id = u.id;

-- Insert sample data for testing (optional - remove in production)
-- INSERT INTO feedback (
--     biggest_hurdle, primary_motivation, time_consuming_part, professional_fear,
--     monetization_considerations, professional_legacy, platform_impact,
--     ip_address
-- ) VALUES (
--     'A', 'B', 'A', 'A',
--     'The main consideration is ensuring compliance with bar association rules while maintaining professional integrity. Time constraints also make it difficult to explore monetization opportunities.',
--     'I want to be remembered as someone who made legal knowledge more accessible to the general public. Sharing knowledge helps build a lasting impact beyond individual cases.',
--     'An effortless platform would allow me to focus on content creation rather than technical barriers. This could significantly expand my reach and establish thought leadership in my practice area.',
--     '127.0.0.1'
-- );

-- Verify table creation
SELECT 'Feedback table created successfully' as status;
SELECT COUNT(*) as feedback_count FROM feedback;
SELECT * FROM feedback_analytics;
