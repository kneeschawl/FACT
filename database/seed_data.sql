USE fiscal_db;

INSERT INTO scraped_products (
    timestamp_recorded, 
    product_id, 
    source_url, 
    product_name, 
    actual_price, 
    discount_percentage, 
    discounted_price, 
    claimed_anchor, 
    urgency_text
) VALUES 
(
    NOW(), 
    'ULT-B211-01', 
    'https://daraz.com.np/products/ultima-boom-211-i12345.html', 
    'Ultima Boom 211 Earbuds with App Support', 
    3599.00, 
    55.57, 
    1599.00, 
    3599.00, 
    'Hurry up! Only 3 items left in stock!'
),
(
    NOW(), 
    'GB-PRO-ANC', 
    'https://daraz.com.np/products/green-buds-pro-anc-i67890.html', 
    'Green Buds Pro ANC (UP to 30 dB) Earbuds', 
    3499.00, 
    51.44, 
    1699.00, 
    3499, 
    'Offer ends in 00:45:12'
),
(
    NOW(), 
    'HY300-PROJ', 
    'https://daraz.com.np/products/hy300-freestyle-projector-i11121.html', 
    'HY300 Freestyle Android 11.0 Led Smart 180 Degree Projector 4k support', 
    7500.00, 
    20.00, 
    6000.00, 
    7500, 
    '52 people are viewing this product right now!'
);