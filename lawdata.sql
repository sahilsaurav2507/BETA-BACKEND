-- =====================================================
-- LawVriksh Referral Platform Database Schema
-- MySQL 8.0.39 Compatible
--
-- Author:      Your Name
-- Version:     1.3
-- Last Update: 2025-07-20
-- Description: Final fix for 'Commands out of sync' error
--              by removing all non-breaking space characters.
-- =====================================================

-- -----------------------------------------------------
-- Initial Setup
-- -----------------------------------------------------
CREATE DATABASE IF NOT EXISTS lawvriksh_referral;
USE lawvriksh_referral;

-- For development, it's safe to drop tables for a clean slate.
DROP TABLE IF EXISTS share_events;
DROP TABLE IF EXISTS users;

-- -----------------------------------------------------
-- User and Privilege Management (Optional)
-- -----------------------------------------------------
DROP USER IF EXISTS 'lawuser'@'%';
CREATE USER 'lawuser'@'%' IDENTIFIED BY 'lawpass123';
GRANT ALL PRIVILEGES ON lawvriksh_referral.* TO 'lawuser'@'%';
FLUSH PRIVILEGES;

-- =====================================================
-- TABLE: users
-- =====================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    total_points INT NOT NULL DEFAULT 0,
    shares_count INT NOT NULL DEFAULT 0,
    default_rank INT NULL,
    current_rank INT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_total_points (total_points DESC),
    INDEX idx_users_is_admin (is_admin),
    INDEX idx_users_default_rank (default_rank),
    INDEX idx_users_current_rank (current_rank)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLE: share_events
-- =====================================================
CREATE TABLE share_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    platform ENUM('twitter', 'facebook', 'linkedin', 'instagram', 'whatsapp') NOT NULL,
    points_earned INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_share_events_user_id (user_id),
    INDEX idx_share_events_platform (platform),
    INDEX idx_share_events_user_platform (user_id, platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- SAMPLE DATA
-- =====================================================
-- Password for all users is 'password123' (hashed with bcrypt)
INSERT INTO users (name, email, password_hash, is_active, is_admin) VALUES
('John Doe', 'john@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, FALSE),
('Jane Smith', 'jane@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, FALSE),
('Admin User', 'admin@lawvriksh.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, TRUE),
('Mike Johnson', 'mike@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, FALSE),
('Sarah Wilson', 'sarah@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO', TRUE, FALSE);

-- =====================================================
-- STORED PROCEDURES
-- =====================================================
DELIMITER //

DROP PROCEDURE IF EXISTS sp_UpdateUserStats//
CREATE PROCEDURE sp_UpdateUserStats(IN p_user_id INT, IN p_points_to_add INT)
BEGIN
    UPDATE users
    SET total_points = total_points + p_points_to_add,
        shares_count = shares_count + 1
    WHERE id = p_user_id;
END//

DROP PROCEDURE IF EXISTS sp_GetUserRank//
CREATE PROCEDURE sp_GetUserRank(IN p_user_id INT)
BEGIN
    SELECT rank_info.*
    FROM (
        SELECT
            u.id,
            u.name,
            u.total_points,
            ROW_NUMBER() OVER (ORDER BY total_points DESC) AS user_rank
        FROM users u
        WHERE u.is_admin = FALSE
    ) AS rank_info
    WHERE rank_info.id = p_user_id;
END//

DROP PROCEDURE IF EXISTS sp_GetLeaderboard//
CREATE PROCEDURE sp_GetLeaderboard(IN p_page INT, IN p_limit INT)
BEGIN
    DECLARE v_offset INT;
    IF p_page < 1 THEN SET p_page = 1; END IF;
    IF p_limit < 1 THEN SET p_limit = 10; END IF;
    SET v_offset = (p_page - 1) * p_limit;
    SELECT
        u.id,
        u.name,
        u.email,
        u.total_points,
        u.shares_count,
        ROW_NUMBER() OVER (ORDER BY u.total_points DESC) as user_rank
    FROM users u
    WHERE u.is_admin = FALSE
    ORDER BY u.total_points DESC
    LIMIT p_limit OFFSET v_offset;
END//

DELIMITER ;

-- =====================================================
-- TRIGGERS
-- =====================================================
DELIMITER //

DROP TRIGGER IF EXISTS trg_after_share_event_insert//
CREATE TRIGGER trg_after_share_event_insert
AFTER INSERT ON share_events
FOR EACH ROW
BEGIN
    CALL sp_UpdateUserStats(NEW.user_id, NEW.points_earned);
END//

DELIMITER ;

-- These inserts will now fire the trigger correctly.
INSERT INTO share_events (user_id, platform, points_earned) VALUES
(1, 'twitter', 1), (1, 'facebook', 3), (1, 'linkedin', 5),
(2, 'instagram', 2), (2, 'twitter', 1),
(4, 'facebook', 3), (4, 'linkedin', 5), (4, 'instagram', 2), (4, 'twitter', 1),
(5, 'facebook', 3), (5, 'linkedin', 5);

-- =====================================================
-- VIEWS
-- =====================================================
DROP VIEW IF EXISTS view_user_stats;
CREATE VIEW view_user_stats AS
SELECT
    u.id,
    u.name,
    u.email,
    u.total_points,
    u.shares_count,
    u.is_admin,
    COUNT(se.id) as total_share_events,
    MAX(se.created_at) as last_share_date
FROM users u
LEFT JOIN share_events se ON u.id = se.user_id
GROUP BY u.id;

DROP VIEW IF EXISTS view_platform_stats;
CREATE VIEW view_platform_stats AS
SELECT
    se.platform,
    COUNT(*) as total_shares,
    SUM(se.points_earned) as total_points,
    COUNT(DISTINCT se.user_id) as unique_users,
    AVG(se.points_earned) as avg_points_per_share
FROM share_events se
GROUP BY se.platform;

-- =====================================================
-- TABLE: feedback
-- =====================================================
CREATE TABLE feedback (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- SCRIPT EXECUTION COMPLETE
-- =====================================================
