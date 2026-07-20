-- Create database container
CREATE DATABASE IF NOT EXISTS fiscal_db;
USE fiscal_db;

CREATE TABLE IF NOT EXISTS scraped_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scraped_at DATE NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    source_url TEXT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    actual_price DECIMAL(10, 2) NOT NULL,
    discount_percentage DECIMAL(5, 2) DEFAULT 0.00,
    discounted_price DECIMAL(10, 2) NOT NULL,
    claimed_anchor DECIMAL(10,2),
    urgency_text TEXT,
    INDEX idx_product_id (product_id),
    INDEX idx_actual_price (actual_price)
);