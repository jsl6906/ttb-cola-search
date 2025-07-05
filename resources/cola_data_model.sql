CREATE TABLE IF NOT EXISTS "colas" (
  "cola_id" bigint PRIMARY KEY,
  "permit_num" varchar,
  "serial_num" varchar,
  "brand_name" varchar,
  "fanciful_name" varchar,
  "origin_code" integer,
  "origin" varchar,
  "class_type_code" integer,
  "class_type" varchar,
  "completed_date" date,
  "scraped_on" datetime,
  "image_count_to_parse" int
);

CREATE TABLE IF NOT EXISTS "cola_analysis" (
  "cola_id" bigint,
  "analysis_model" varchar,
  "analysis_type" varchar,
  "model_version" varchar,
  "analysis_completed_on" datetime,
  "prompt" varchar,
  "response" json,
  "metadata" json,
  PRIMARY KEY ("cola_id", "analysis_model")
);

CREATE TABLE IF NOT EXISTS "cola_images" (
  "cola_id" bigint,
  "file_name" varchar,
  "img_type" varchar,
  "width_px" int,
  "height_px" int,
  "dimensions_txt" varchar,
  "local_path" varchar,
  "scraped_on" datetime,
  PRIMARY KEY ("cola_id", "file_name")
);

CREATE TABLE IF NOT EXISTS "cola_image_analysis" (
  "cola_id" bigint,
  "file_name" varchar,
  "analysis_model" varchar,
  "model_version" varchar,
  "analysis_completed_on" datetime,
  "metadata" json,
  PRIMARY KEY ("cola_id", "file_name", "analysis_model")
);

CREATE TABLE IF NOT EXISTS "image_analysis_items" (
  "id" bigint PRIMARY KEY,
  "cola_id" bigint,
  "file_name" varchar,
  "analysis_model" varchar,
  "analysis_item_type" varchar,
  "text" varchar,
  "model_confidence" float,
  "bounding_box" json
);

COMMENT ON COLUMN "colas"."scraped_on" IS 'the date the cola characteristic data was scraped from the public COLA registry';
COMMENT ON COLUMN "cola_images"."width_px" IS 'the pixel width as represented in the html <img> tag from the public COLA registry';
COMMENT ON COLUMN "cola_images"."height_px" IS 'the pixel height as represented in the html <img> tag from the public COLA registry';
COMMENT ON COLUMN "cola_images"."dimensions_txt" IS 'the dimensions present on the COLA form printout page, presumably entered by the submitter of the label';
COMMENT ON COLUMN "cola_images"."local_path" IS 'the local, relative path of the image file';
COMMENT ON COLUMN "cola_images"."scraped_on" IS 'the date the cola image characteristic data was scraped from the public COLA registry';
COMMENT ON COLUMN "cola_image_analysis"."analysis_model" IS 'the model used to produce the analysis output';
COMMENT ON COLUMN "cola_image_analysis"."model_version" IS 'the version of the analysis model used';
COMMENT ON COLUMN "cola_image_analysis"."analysis_completed_on" IS 'the date the analysis was completed';
COMMENT ON COLUMN "image_analysis_items"."analysis_item_type" IS 'e.g., tag, caption, object, text block, text line, etc.';
COMMENT ON COLUMN "cola_analysis"."analysis_type" IS 'the type of analysis performed, e.g., consistency, term_match, product classification, etc.';

CREATE OR REPLACE VIEW vw_colas as
  SELECT
    colas.*,
    CASE
      WHEN UPPER(colas.class_type) LIKE '%WINE%'
        OR UPPER(colas.class_type) LIKE '%CIDER%'
        OR UPPER(colas.class_type) LIKE '%MEAD%'
        OR UPPER(colas.class_type) LIKE '%SAKE%'
        THEN 'wine'
      WHEN UPPER(colas.class_type) LIKE '%BEER%'
        OR UPPER(colas.class_type) LIKE '%MALT BEV%'
        OR UPPER(colas.class_type) LIKE '%ALE%'
        OR UPPER(colas.class_type) LIKE '%PORTER%'
        THEN 'beer'
      WHEN colas.class_type IS NULL OR TRIM(colas.class_type) = '' 
        THEN 'unknown'
      ELSE 'distilled_spirits'
    END as ct_commodity,
    CASE
      WHEN (
        UPPER(colas.origin) IN ('AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 
          'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 
          'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 
          'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC', 'USA',
          'ALABAMA', 'ALASKA', 'ARIZONA', 'ARKANSAS', 'CALIFORNIA', 'COLORADO', 'CONNECTICUT', 
          'DELAWARE', 'FLORIDA', 'GEORGIA', 'HAWAII', 'IDAHO', 'ILLINOIS', 'INDIANA', 'IOWA', 
          'KANSAS', 'KENTUCKY', 'LOUISIANA', 'MAINE', 'MARYLAND', 'MASSACHUSETTS', 'MICHIGAN', 
          'MINNESOTA', 'MISSISSIPPI', 'MISSOURI', 'MONTANA', 'NEBRASKA', 'NEVADA', 'NEW HAMPSHIRE', 
          'NEW JERSEY', 'NEW MEXICO', 'NEW YORK', 'NORTH CAROLINA', 'NORTH DAKOTA', 'OHIO', 'OKLAHOMA', 
          'OREGON', 'PENNSYLVANIA', 'RHODE ISLAND', 'SOUTH CAROLINA', 'SOUTH DAKOTA', 'TENNESSEE', 
          'TEXAS', 'UTAH', 'VERMONT', 'VIRGINIA', 'WASHINGTON', 'WEST VIRGINIA', 'WISCONSIN', 'WYOMING',
          'DISTRICT OF COLUMBIA', 'AMERICAN')
      ) THEN 'domestic'
      WHEN UPPER(colas.class_type) LIKE '%IMPORT%'
        OR UPPER(colas.class_type) LIKE '%FOREIGN%'
        THEN 'import'
      WHEN colas.origin IS NULL OR TRIM(colas.origin) = '' 
        THEN 'unknown'
      ELSE 'import'
    END as ct_source,
    'https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicDisplaySearchBasic&ttbid=' || colas.cola_id as cola_details_url,
    'https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicFormDisplay&ttbid=' || colas.cola_id as cola_form_url,
    'https://int.ttbonline.gov/colasonline/viewColaDetails.do?action=internalDisplay&ttbid=' || colas.cola_id as cola_internal_url,
    COUNT(cola_analysis.cola_id) as cola_analysis_count,
    COUNT(CASE WHEN json_array_length(cola_analysis.response->'violations') > 0 THEN 1 END) as cola_analysis_with_violations_count,
    COUNT(cola_images.file_name) as parsed_image_count,
    COUNT(CASE WHEN cola_images.local_path IS NOT NULL THEN 1 END) as downloaded_image_count,
    COUNT(cola_image_analysis.cola_id) as image_analysis_count
  FROM colas
  LEFT JOIN cola_analysis on colas.cola_id = cola_analysis.cola_id
  LEFT JOIN cola_images ON colas.cola_id = cola_images.cola_id
  LEFT JOIN cola_image_analysis ON cola_images.cola_id = cola_image_analysis.cola_id and cola_images.file_name = cola_image_analysis.file_name
  GROUP BY ALL
  ORDER BY completed_date desc;

CREATE OR REPLACE VIEW vw_cola_images as
  SELECT
    cola_images.*,
    REPLACE(REPLACE(local_path, 'raw_images\', 'https://storage.googleapis.com/ttb-cola-images/'), '\', '/') as public_url
  FROM cola_images;

CREATE OR REPLACE VIEW vw_cola_violations_list as
  SELECT
    ca.cola_id,
    ca.cola_form_url,
    ca.cola_internal_url,
    ca.ct_commodity,
    ca.ct_source,
    v.value ->> 'comment' AS violation_comment,
    v.value ->> 'rule_type' AS violation_type,
    v.value ->> 'rule_group' AS violation_group,
    v.value ->> 'rule_subgroup' AS violation_subgroup,
    ca.brand_name,
    UPPER(ca.response->>'brand_name') AS analysis_brand_name,
    ca.class_type,
    UPPER(ca.response->>'class_type') AS analysis_class_type,
    ca.analysis_model,
    ca.analysis_type,
    ca.model_version,
    ca.analysis_completed_on,
    ca.prompt,
    ca.response,
    ca.metadata->'total_token_count' AS analysis_token_count
  FROM (
    select *
    FROM cola_analysis 
    LEFT JOIN vw_colas ON vw_colas.cola_id = cola_analysis.cola_id
  ) ca,
  LATERAL json_each(ca.response->'violations') AS v
  WHERE ca.response IS NOT NULL
  ORDER BY analysis_completed_on DESC;

CREATE OR REPLACE VIEW vw_llm_summary as
  SELECT
    analysis_model,
    model_version,
    analysis_type,
    COUNT(*) AS total_colas_analyzed,
    COUNT(CASE WHEN json_array_length(response->'violations') > 0 THEN 1 END) AS num_colas_with_violations,
    num_colas_with_violations * 100.0 / COUNT(*) AS percent_colas_with_violations,
    SUM(CAST(metadata->>'candidates_token_count' AS INTEGER)) AS total_candidates_tokens,
    SUM(CAST(metadata->>'prompt_token_count' AS INTEGER)) AS total_prompt_tokens,
    SUM(CAST(metadata->>'total_token_count' AS INTEGER)) AS total_all_tokens
  FROM cola_analysis
  WHERE response IS NOT NULL
  GROUP BY analysis_model, model_version, analysis_type
  ORDER BY total_colas_analyzed DESC;

CREATE OR REPLACE VIEW vw_image_analysis_summary AS
  SELECT
    analysis_item_type,
    text,
    COUNT(*) AS count,
    RANK() OVER (
      PARTITION BY analysis_item_type
      ORDER BY COUNT(*) DESC
    ) AS item_type_rank,
    MIN(colas.completed_date) as first_completed_date,
    MAX(colas.completed_date) as last_completed_date
  FROM image_analysis_items
  LEFT JOIN colas on image_analysis_items.cola_id = colas.cola_id
  GROUP BY analysis_item_type, text
  ORDER BY analysis_item_type, item_type_rank
;