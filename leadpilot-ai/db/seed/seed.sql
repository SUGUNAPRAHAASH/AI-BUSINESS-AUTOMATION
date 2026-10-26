-- Seed data for LeadPilot AI (BrightSmile Dental tenant & initial inventory)

INSERT INTO tenants (id, name, slug, settings)
VALUES (
  'a0000000-0000-0000-0000-000000000001',
  'BrightSmile Dental',
  'brightsmile',
  '{"timezone": "America/New_York", "currency": "USD", "cancellation_notice_hours": 24, "emergency_phone": "+1-555-0199"}'::jsonb
)
ON CONFLICT (slug) DO UPDATE
SET name = EXCLUDED.name, settings = EXCLUDED.settings;

-- Inventory items for BrightSmile Dental store
INSERT INTO inventory (sku, name, stock, low_stock_threshold) VALUES
('SKU-WKIT-01', 'Professional At-Home Whitening Kit', 24, 5),
('SKU-TOOTH-02', 'UltraSonic Electric Toothbrush Pro', 12, 4),
('SKU-PASTE-03', 'Enamel Restoration Remineralizing Toothpaste', 45, 10),
('SKU-FLOSS-04', 'Water Flosser Cordless Advanced', 3, 5), -- Low stock sample
('SKU-GUARD-05', 'Custom Night Guard Protection Set', 18, 5)
ON CONFLICT (sku) DO UPDATE
SET name = EXCLUDED.name, stock = EXCLUDED.stock, low_stock_threshold = EXCLUDED.low_stock_threshold;
