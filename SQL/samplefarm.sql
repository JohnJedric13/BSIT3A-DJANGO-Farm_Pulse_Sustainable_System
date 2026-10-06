-- STREAMING_CHUNK:Configuring AgriCare table structures for bsitcrud...

--
-- Database: `bsitcrud`
--

-- --------------------------------------------------------
-- Table structure for table `crops`
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS `crops` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL,
  `crop_type` varchar(100) NOT NULL,
  `location` varchar(150) NOT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'Healthy',
  `last_observation` text DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `crops_user_id_fk_auth_user_id` (`user_id`),
  CONSTRAINT `crops_user_id_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table structure for table `farm_logs`
-- --------------------------------------------------------

-- STREAMING_CHUNK:Creating farm_logs table for daily activities...

CREATE TABLE IF NOT EXISTS `farm_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `crop_id` int(11) NOT NULL,
  `activity_type` varchar(100) NOT NULL,
  `observed_condition` varchar(50) NOT NULL,
  `notes` text NOT NULL,
  `log_date` date NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `farm_logs_crop_id_fk_crops_id` (`crop_id`),
  CONSTRAINT `farm_logs_crop_id_fk_crops_id` FOREIGN KEY (`crop_id`) REFERENCES `crops` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Table structure for table `ai_diagnoses`
-- --------------------------------------------------------

-- STREAMING_CHUNK:Creating ai_diagnoses table for AI reports...

CREATE TABLE IF NOT EXISTS `ai_diagnoses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `crop_id` int(11) NOT NULL,
  `log_id` int(11) DEFAULT NULL,
  `symptom_summary` text NOT NULL,
  `diagnosis_title` varchar(255) NOT NULL,
  `treatment_plan` text NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `ai_diagnoses_crop_id_fk_crops_id` (`crop_id`),
  KEY `ai_diagnoses_log_id_fk_farm_logs_id` (`log_id`),
  CONSTRAINT `ai_diagnoses_crop_id_fk_crops_id` FOREIGN KEY (`crop_id`) REFERENCES `crops` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ai_diagnoses_log_id_fk_farm_logs_id` FOREIGN KEY (`log_id`) REFERENCES `farm_logs` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- Dumping initial seed data for test user (glenn, user_id = 1)
-- --------------------------------------------------------

-- STREAMING_CHUNK:Inserting seed sample data...

INSERT INTO `crops` (`id`, `user_id`, `name`, `crop_type`, `location`, `status`, `last_observation`, `created_at`) VALUES
(1, 1, 'Tomato Field A', 'Roma Tomato', 'North Greenhouse', 'Unhealthy', 'Yellow concentric rings on lower foliage', NOW()),
(2, 1, 'Corn Patch #1', 'Sweet Corn', 'East Field', 'Healthy', 'Good stalk growth, normal dark green color', NOW()),
(3, 1, 'Rice Paddy B', 'Jasmine Rice', 'South Terraces', 'Minor Warning', 'Soil moisture slightly low, leaf tips browning', NOW());

INSERT INTO `farm_logs` (`id`, `crop_id`, `activity_type`, `observed_condition`, `notes`, `log_date`, `created_at`) VALUES
(1, 1, 'Field Inspection', 'Unhealthy / Sick', 'Noticed yellow concentric spots with brown centers on bottom leaves. Possible fungal infection.', CURDATE(), NOW()),
(2, 2, 'Watering / Irrigation', 'Healthy', 'Drip irrigation ran for 45 mins. Soil moisture optimal.', CURDATE(), NOW());

COMMIT;