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
-- TABLE: users (Optimized for Performance)
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

    -- Primary and unique indexes
    INDEX idx_users_email (email),

    -- Performance-critical indexes for leaderboard queries
    INDEX idx_users_leaderboard (total_points DESC, created_at ASC, is_admin),
    INDEX idx_users_total_points_desc (total_points DESC),
    INDEX idx_users_active_users (is_active, is_admin, total_points DESC),

    -- Ranking indexes
    INDEX idx_users_default_rank (default_rank),
    INDEX idx_users_current_rank (current_rank),
    INDEX idx_users_rank_comparison (default_rank, current_rank),

    -- Admin and filtering indexes
    INDEX idx_users_is_admin (is_admin),
    INDEX idx_users_active_status (is_active),

    -- Composite indexes for common query patterns
    INDEX idx_users_points_created (total_points DESC, created_at ASC),
    INDEX idx_users_non_admin_points (is_admin, total_points DESC, created_at ASC),

    -- Time-based indexes for analytics
    INDEX idx_users_created_at (created_at),
    INDEX idx_users_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLE: share_events (Optimized for Performance)
-- =====================================================
CREATE TABLE share_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    platform ENUM('twitter', 'facebook', 'linkedin', 'instagram', 'whatsapp') NOT NULL,
    points_earned INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Performance-critical indexes
    INDEX idx_share_events_user_id (user_id),
    INDEX idx_share_events_platform (platform),
    INDEX idx_share_events_user_platform (user_id, platform),

    -- Composite indexes for common query patterns
    INDEX idx_share_events_user_created (user_id, created_at DESC),
    INDEX idx_share_events_platform_created (platform, created_at DESC),
    INDEX idx_share_events_user_platform_created (user_id, platform, created_at DESC),

    -- Analytics indexes
    INDEX idx_share_events_created_at (created_at DESC),
    INDEX idx_share_events_points_earned (points_earned),
    INDEX idx_share_events_platform_points (platform, points_earned),

    -- Covering index for share history queries
    INDEX idx_share_events_covering (user_id, platform, points_earned, created_at DESC)
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

    -- Use optimized query with better indexing
    SELECT
        u.id,
        u.name,
        u.email,
        u.total_points,
        u.shares_count,
        u.default_rank,
        u.current_rank,
        ROW_NUMBER() OVER (ORDER BY u.total_points DESC, u.created_at ASC) as user_rank,
        CASE
            WHEN u.default_rank IS NOT NULL AND u.current_rank IS NOT NULL
            THEN u.default_rank - u.current_rank
            WHEN u.default_rank IS NOT NULL
            THEN u.default_rank - ROW_NUMBER() OVER (ORDER BY u.total_points DESC, u.created_at ASC)
            ELSE 0
        END as rank_improvement
    FROM users u
    WHERE u.is_admin = FALSE
    ORDER BY u.total_points DESC, u.created_at ASC
    LIMIT p_limit OFFSET v_offset;
END//

-- Procedure to refresh materialized leaderboard
DROP PROCEDURE IF EXISTS sp_RefreshMaterializedLeaderboard//
CREATE PROCEDURE sp_RefreshMaterializedLeaderboard()
BEGIN
    -- Clear existing data
    TRUNCATE TABLE materialized_leaderboard;

    -- Populate with fresh data
    INSERT INTO materialized_leaderboard (
        user_id, name, email, total_points, shares_count,
        user_rank, default_rank, current_rank, rank_improvement
    )
    SELECT
        u.id,
        u.name,
        u.email,
        u.total_points,
        u.shares_count,
        ROW_NUMBER() OVER (ORDER BY u.total_points DESC, u.created_at ASC) as user_rank,
        u.default_rank,
        u.current_rank,
        CASE
            WHEN u.default_rank IS NOT NULL AND u.current_rank IS NOT NULL
            THEN u.default_rank - u.current_rank
            WHEN u.default_rank IS NOT NULL
            THEN u.default_rank - ROW_NUMBER() OVER (ORDER BY u.total_points DESC, u.created_at ASC)
            ELSE 0
        END as rank_improvement
    FROM users u
    WHERE u.is_admin = FALSE
    ORDER BY u.total_points DESC, u.created_at ASC;
END//

-- Procedure to update user analytics summary
DROP PROCEDURE IF EXISTS sp_UpdateUserAnalytics//
CREATE PROCEDURE sp_UpdateUserAnalytics(IN p_user_id INT)
BEGIN
    INSERT INTO user_analytics_summary (
        user_id, total_shares, total_points, platforms_used,
        first_share_date, last_share_date, avg_points_per_share, most_used_platform
    )
    SELECT
        p_user_id,
        COUNT(*) as total_shares,
        SUM(points_earned) as total_points,
        COUNT(DISTINCT platform) as platforms_used,
        MIN(created_at) as first_share_date,
        MAX(created_at) as last_share_date,
        AVG(points_earned) as avg_points_per_share,
        (SELECT platform FROM share_events se2
         WHERE se2.user_id = p_user_id
         GROUP BY platform
         ORDER BY COUNT(*) DESC
         LIMIT 1) as most_used_platform
    FROM share_events se
    WHERE se.user_id = p_user_id
    ON DUPLICATE KEY UPDATE
        total_shares = VALUES(total_shares),
        total_points = VALUES(total_points),
        platforms_used = VALUES(platforms_used),
        first_share_date = VALUES(first_share_date),
        last_share_date = VALUES(last_share_date),
        avg_points_per_share = VALUES(avg_points_per_share),
        most_used_platform = VALUES(most_used_platform),
        last_updated = CURRENT_TIMESTAMP;
END//

DELIMITER ;

-- =====================================================
-- ENHANCED TRIGGERS FOR PERFORMANCE
-- =====================================================
DELIMITER //

-- Enhanced trigger for share event inserts
DROP TRIGGER IF EXISTS trg_after_share_event_insert//
CREATE TRIGGER trg_after_share_event_insert
AFTER INSERT ON share_events
FOR EACH ROW
BEGIN
    -- Update user stats (existing functionality)
    CALL sp_UpdateUserStats(NEW.user_id, NEW.points_earned);

    -- Update user analytics summary
    CALL sp_UpdateUserAnalytics(NEW.user_id);
END//

-- Trigger for share event updates
DROP TRIGGER IF EXISTS trg_after_share_event_update//
CREATE TRIGGER trg_after_share_event_update
AFTER UPDATE ON share_events
FOR EACH ROW
BEGIN
    -- Update analytics if points changed
    IF OLD.points_earned != NEW.points_earned THEN
        -- Adjust user stats
        UPDATE users
        SET total_points = total_points - OLD.points_earned + NEW.points_earned
        WHERE id = NEW.user_id;

        -- Update analytics
        CALL sp_UpdateUserAnalytics(NEW.user_id);
    END IF;
END//

-- Trigger for share event deletes
DROP TRIGGER IF EXISTS trg_after_share_event_delete//
CREATE TRIGGER trg_after_share_event_delete
AFTER DELETE ON share_events
FOR EACH ROW
BEGIN
    -- Adjust user stats
    UPDATE users
    SET total_points = total_points - OLD.points_earned,
        shares_count = shares_count - 1
    WHERE id = OLD.user_id;

    -- Update analytics
    CALL sp_UpdateUserAnalytics(OLD.user_id);
END//

DELIMITER ;

-- These inserts will now fire the trigger correctly.
INSERT INTO share_events (user_id, platform, points_earned) VALUES
(1, 'twitter', 1), (1, 'facebook', 3), (1, 'linkedin', 5),
(2, 'instagram', 2), (2, 'twitter', 1),
(4, 'facebook', 3), (4, 'linkedin', 5), (4, 'instagram', 2), (4, 'twitter', 1),
(5, 'facebook', 3), (5, 'linkedin', 5);

-- =====================================================
-- OPTIMIZED VIEWS AND MATERIALIZED VIEWS
-- =====================================================

-- Enhanced user stats view with performance optimizations
DROP VIEW IF EXISTS view_user_stats;
CREATE VIEW view_user_stats AS
SELECT
    u.id,
    u.name,
    u.email,
    u.total_points,
    u.shares_count,
    u.is_admin,
    u.default_rank,
    u.current_rank,
    COALESCE(se_stats.total_share_events, 0) as total_share_events,
    se_stats.last_share_date,
    se_stats.first_share_date,
    CASE
        WHEN u.default_rank IS NOT NULL AND u.current_rank IS NOT NULL
        THEN u.default_rank - u.current_rank
        ELSE 0
    END as rank_improvement
FROM users u
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) as total_share_events,
        MAX(created_at) as last_share_date,
        MIN(created_at) as first_share_date
    FROM share_events
    GROUP BY user_id
) se_stats ON u.id = se_stats.user_id;

-- Enhanced platform stats view
DROP VIEW IF EXISTS view_platform_stats;
CREATE VIEW view_platform_stats AS
SELECT
    se.platform,
    COUNT(*) as total_shares,
    SUM(se.points_earned) as total_points,
    COUNT(DISTINCT se.user_id) as unique_users,
    AVG(se.points_earned) as avg_points_per_share,
    MAX(se.created_at) as last_share_date,
    MIN(se.created_at) as first_share_date
FROM share_events se
GROUP BY se.platform;

-- Leaderboard materialized view (simulated with table for MySQL)
DROP TABLE IF EXISTS materialized_leaderboard;
CREATE TABLE materialized_leaderboard (
    user_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    total_points INT NOT NULL,
    shares_count INT NOT NULL,
    user_rank INT NOT NULL,
    default_rank INT NULL,
    current_rank INT NULL,
    rank_improvement INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_materialized_rank (user_rank),
    INDEX idx_materialized_points (total_points DESC),
    INDEX idx_materialized_updated (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User analytics summary table for fast dashboard queries
DROP TABLE IF EXISTS user_analytics_summary;
CREATE TABLE user_analytics_summary (
    user_id INT PRIMARY KEY,
    total_shares INT DEFAULT 0,
    total_points INT DEFAULT 0,
    platforms_used INT DEFAULT 0,
    first_share_date TIMESTAMP NULL,
    last_share_date TIMESTAMP NULL,
    avg_points_per_share DECIMAL(10,2) DEFAULT 0.00,
    most_used_platform VARCHAR(20) NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_analytics_points (total_points DESC),
    INDEX idx_analytics_shares (total_shares DESC),
    INDEX idx_analytics_updated (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
-- PERFORMANCE MONITORING AND MAINTENANCE
-- =====================================================

-- Create performance monitoring table
DROP TABLE IF EXISTS query_performance_log;
CREATE TABLE query_performance_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    query_type VARCHAR(50) NOT NULL,
    execution_time_ms DECIMAL(10,3) NOT NULL,
    rows_examined INT DEFAULT 0,
    rows_returned INT DEFAULT 0,
    query_hash VARCHAR(64) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_perf_query_type (query_type),
    INDEX idx_perf_execution_time (execution_time_ms),
    INDEX idx_perf_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DELIMITER //

-- Procedure for database maintenance and optimization
DROP PROCEDURE IF EXISTS sp_DatabaseMaintenance//
CREATE PROCEDURE sp_DatabaseMaintenance()
BEGIN
    -- Refresh materialized leaderboard
    CALL sp_RefreshMaterializedLeaderboard();

    -- Update all user analytics
    INSERT INTO user_analytics_summary (user_id)
    SELECT DISTINCT u.id FROM users u
    WHERE u.id NOT IN (SELECT user_id FROM user_analytics_summary)
    ON DUPLICATE KEY UPDATE user_id = VALUES(user_id);

    -- Clean old performance logs (keep last 7 days)
    DELETE FROM query_performance_log
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);

    -- Analyze tables for query optimization
    ANALYZE TABLE users, share_events, materialized_leaderboard, user_analytics_summary;
END//

-- Procedure to get performance statistics
DROP PROCEDURE IF EXISTS sp_GetPerformanceStats//
CREATE PROCEDURE sp_GetPerformanceStats()
BEGIN
    SELECT
        query_type,
        COUNT(*) as query_count,
        AVG(execution_time_ms) as avg_execution_time,
        MAX(execution_time_ms) as max_execution_time,
        MIN(execution_time_ms) as min_execution_time,
        AVG(rows_examined) as avg_rows_examined,
        AVG(rows_returned) as avg_rows_returned
    FROM query_performance_log
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY query_type
    ORDER BY avg_execution_time DESC;
END//

-- Procedure for fast leaderboard using materialized view
DROP PROCEDURE IF EXISTS sp_GetFastLeaderboard//
CREATE PROCEDURE sp_GetFastLeaderboard(IN p_page INT, IN p_limit INT)
BEGIN
    DECLARE v_offset INT;
    IF p_page < 1 THEN SET p_page = 1; END IF;
    IF p_limit < 1 THEN SET p_limit = 10; END IF;
    SET v_offset = (p_page - 1) * p_limit;

    -- Use materialized leaderboard for ultra-fast queries
    SELECT
        user_id,
        name,
        email,
        total_points,
        shares_count,
        user_rank,
        default_rank,
        current_rank,
        rank_improvement
    FROM materialized_leaderboard
    ORDER BY user_rank
    LIMIT p_limit OFFSET v_offset;
END//

DELIMITER ;

-- Initialize materialized views with current data
CALL sp_RefreshMaterializedLeaderboard();

-- Populate user analytics for existing users
INSERT INTO user_analytics_summary (user_id)
SELECT DISTINCT id FROM users
ON DUPLICATE KEY UPDATE user_id = VALUES(user_id);

-- =====================================================
-- SCRIPT EXECUTION COMPLETE
-- =====================================================
