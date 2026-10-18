-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: healthcare_claims
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `claim_documents`
--

DROP TABLE IF EXISTS `claim_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `claim_documents` (
  `document_id` int NOT NULL AUTO_INCREMENT,
  `original_filename` varchar(255) NOT NULL,
  `stored_filename` varchar(255) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `status` enum('QUEUED','PROCESSING','VALIDATED','NEEDS_REVIEW','DUPLICATE','FAILED') NOT NULL DEFAULT 'QUEUED',
  `processing_status` enum('QUEUED','PROCESSING','COMPLETED','FAILED') NOT NULL DEFAULT 'QUEUED',
  `validation_status` enum('VALIDATED','NEEDS_REVIEW','DUPLICATE') DEFAULT NULL,
  `upload_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`document_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `claims`
--

DROP TABLE IF EXISTS `claims`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `claims` (
  `id` text,
  `patientid` text,
  `providerid` text,
  `primarypatientinsuranceid` text,
  `secondarypatientinsuranceid` text,
  `departmentid` bigint DEFAULT NULL,
  `patientdepartmentid` bigint DEFAULT NULL,
  `diagnosis1` bigint DEFAULT NULL,
  `diagnosis2` double DEFAULT NULL,
  `diagnosis3` double DEFAULT NULL,
  `diagnosis4` double DEFAULT NULL,
  `diagnosis5` double DEFAULT NULL,
  `diagnosis6` double DEFAULT NULL,
  `diagnosis7` double DEFAULT NULL,
  `diagnosis8` double DEFAULT NULL,
  `referringproviderid` double DEFAULT NULL,
  `appointmentid` text,
  `currentillnessdate` text,
  `servicedate` text,
  `supervisingproviderid` text,
  `status1` text,
  `status2` text,
  `statusp` text,
  `outstanding1` double DEFAULT NULL,
  `outstanding2` double DEFAULT NULL,
  `outstandingp` double DEFAULT NULL,
  `lastbilleddate1` text,
  `lastbilleddate2` text,
  `lastbilleddatep` text,
  `healthcareclaimtypeid1` bigint DEFAULT NULL,
  `healthcareclaimtypeid2` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `claims_transactions`
--

DROP TABLE IF EXISTS `claims_transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `claims_transactions` (
  `id` text,
  `claimid` text,
  `chargeid` bigint DEFAULT NULL,
  `patientid` text,
  `type` text,
  `amount` double DEFAULT NULL,
  `method` text,
  `fromdate` text,
  `todate` text,
  `placeofservice` text,
  `procedurecode` bigint DEFAULT NULL,
  `modifier1` double DEFAULT NULL,
  `modifier2` double DEFAULT NULL,
  `diagnosisref1` bigint DEFAULT NULL,
  `diagnosisref2` double DEFAULT NULL,
  `diagnosisref3` double DEFAULT NULL,
  `diagnosisref4` double DEFAULT NULL,
  `units` bigint DEFAULT NULL,
  `departmentid` bigint DEFAULT NULL,
  `notes` text,
  `unitamount` double DEFAULT NULL,
  `transferoutid` double DEFAULT NULL,
  `transfertype` text,
  `payments` double DEFAULT NULL,
  `adjustments` double DEFAULT NULL,
  `transfers` double DEFAULT NULL,
  `outstanding` double DEFAULT NULL,
  `appointmentid` text,
  `linenote` double DEFAULT NULL,
  `patientinsuranceid` text,
  `feescheduleid` bigint DEFAULT NULL,
  `providerid` text,
  `supervisingproviderid` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `encounters`
--

DROP TABLE IF EXISTS `encounters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `encounters` (
  `id` text,
  `start` text,
  `stop` text,
  `patient` text,
  `organization` text,
  `provider` text,
  `payer` text,
  `encounterclass` text,
  `code` bigint DEFAULT NULL,
  `description` text,
  `base_encounter_cost` double DEFAULT NULL,
  `total_claim_cost` double DEFAULT NULL,
  `payer_coverage` double DEFAULT NULL,
  `reasoncode` double DEFAULT NULL,
  `reasondescription` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `extracted_fields`
--

DROP TABLE IF EXISTS `extracted_fields`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `extracted_fields` (
  `extracted_id` int NOT NULL AUTO_INCREMENT,
  `document_id` int NOT NULL,
  `claim_id` varchar(100) DEFAULT NULL,
  `patient_id` varchar(100) DEFAULT NULL,
  `provider_id` varchar(100) DEFAULT NULL,
  `payer_id` varchar(100) DEFAULT NULL,
  `claimed_amount` decimal(15,2) DEFAULT NULL,
  `extracted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`extracted_id`),
  UNIQUE KEY `document_id` (`document_id`),
  CONSTRAINT `extracted_fields_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `claim_documents` (`document_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `organizations`
--

DROP TABLE IF EXISTS `organizations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `organizations` (
  `id` text,
  `name` text,
  `address` text,
  `city` text,
  `state` text,
  `zip` bigint DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `lon` double DEFAULT NULL,
  `phone` text,
  `revenue` double DEFAULT NULL,
  `utilization` bigint DEFAULT NULL,
  `npi` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `patients`
--

DROP TABLE IF EXISTS `patients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patients` (
  `id` text,
  `birthdate` text,
  `deathdate` text,
  `ssn` text,
  `drivers` text,
  `passport` text,
  `prefix` text,
  `first` text,
  `middle` text,
  `last` text,
  `suffix` text,
  `maiden` text,
  `marital` text,
  `race` text,
  `ethnicity` text,
  `gender` text,
  `birthplace` text,
  `address` text,
  `city` text,
  `state` text,
  `county` text,
  `fips` double DEFAULT NULL,
  `zip` bigint DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `lon` double DEFAULT NULL,
  `healthcare_expenses` double DEFAULT NULL,
  `healthcare_coverage` double DEFAULT NULL,
  `income` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `payers`
--

DROP TABLE IF EXISTS `payers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payers` (
  `id` text,
  `name` text,
  `ownership` text,
  `address` double DEFAULT NULL,
  `city` double DEFAULT NULL,
  `state_headquartered` double DEFAULT NULL,
  `zip` double DEFAULT NULL,
  `phone` double DEFAULT NULL,
  `amount_covered` double DEFAULT NULL,
  `amount_uncovered` double DEFAULT NULL,
  `revenue` double DEFAULT NULL,
  `covered_encounters` bigint DEFAULT NULL,
  `uncovered_encounters` bigint DEFAULT NULL,
  `covered_medications` bigint DEFAULT NULL,
  `uncovered_medications` bigint DEFAULT NULL,
  `covered_procedures` bigint DEFAULT NULL,
  `uncovered_procedures` bigint DEFAULT NULL,
  `covered_immunizations` bigint DEFAULT NULL,
  `uncovered_immunizations` bigint DEFAULT NULL,
  `unique_customers` bigint DEFAULT NULL,
  `qols_avg` double DEFAULT NULL,
  `member_months` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `procedures`
--

DROP TABLE IF EXISTS `procedures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `procedures` (
  `start` text,
  `stop` text,
  `patient` text,
  `encounter` text,
  `system` text,
  `code` bigint DEFAULT NULL,
  `description` text,
  `base_cost` double DEFAULT NULL,
  `reasoncode` double DEFAULT NULL,
  `reasondescription` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `processing_events`
--

DROP TABLE IF EXISTS `processing_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `processing_events` (
  `event_id` int NOT NULL AUTO_INCREMENT,
  `document_id` int NOT NULL,
  `event_type` varchar(100) DEFAULT NULL,
  `message` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`event_id`),
  KEY `document_id` (`document_id`),
  CONSTRAINT `processing_events_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `claim_documents` (`document_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `providers`
--

DROP TABLE IF EXISTS `providers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `providers` (
  `id` text,
  `organization` text,
  `name` text,
  `gender` text,
  `speciality` text,
  `address` text,
  `city` text,
  `state` text,
  `zip` bigint DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `lon` double DEFAULT NULL,
  `encounters` bigint DEFAULT NULL,
  `procedures` bigint DEFAULT NULL,
  `npi` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `validation_issues`
--

DROP TABLE IF EXISTS `validation_issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `validation_issues` (
  `issue_id` int NOT NULL AUTO_INCREMENT,
  `document_id` int NOT NULL,
  `field_name` varchar(100) DEFAULT NULL,
  `expected_value` text,
  `extracted_value` text,
  `issue_type` varchar(100) DEFAULT NULL,
  `issue_message` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`issue_id`),
  KEY `document_id` (`document_id`),
  CONSTRAINT `validation_issues_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `claim_documents` (`document_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-18 20:36:32
