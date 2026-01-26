-- Migration: Add CMS Landing Page Fields
-- Add new columns to website_settings table for landing page management

ALTER TABLE website_settings 
ADD COLUMN banner_images JSON NULL AFTER favicon_url,
ADD COLUMN header_background VARCHAR(20) NULL AFTER secondary_color,
ADD COLUMN custom_css TEXT NULL AFTER header_background,
ADD COLUMN custom_js TEXT NULL AFTER custom_css;
