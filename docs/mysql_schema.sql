CREATE DATABASE IF NOT EXISTS ai_factshield CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_factshield;

CREATE TABLE IF NOT EXISTS news_articles (
  id INT PRIMARY KEY AUTO_INCREMENT, title VARCHAR(500) NOT NULL, description TEXT, url VARCHAR(1000),
  source VARCHAR(255), domain VARCHAR(255), provider VARCHAR(100), published_ist VARCHAR(40),
  category VARCHAR(80), city VARCHAR(100) DEFAULT 'Nadiad', fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_news_url (url(255))
);

CREATE TABLE IF NOT EXISTS news_verifications (
  id INT PRIMARY KEY AUTO_INCREMENT, claim LONGTEXT NOT NULL, city VARCHAR(100) DEFAULT 'Nadiad',
  verdict VARCHAR(20) NOT NULL, confidence DOUBLE, evidence_confirmed BOOLEAN DEFAULT FALSE,
  evidence_domains INT DEFAULT 0, explanation TEXT, best_source VARCHAR(255), best_url VARCHAR(1000),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
