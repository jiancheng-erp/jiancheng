CREATE DATABASE  IF NOT EXISTS `jiancheng` /*!40100 DEFAULT CHARACTER SET utf8mb3 */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `jiancheng`;
-- MySQL dump 10.13  Distrib 8.0.40, for Linux (x86_64)
--
-- Host: localhost    Database: jiancheng
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `assets_purchase_order_item`
--

DROP TABLE IF EXISTS `assets_purchase_order_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assets_purchase_order_item` (
  `assets_purchase_order_item_id` bigint NOT NULL AUTO_INCREMENT,
  `material_id` bigint NOT NULL,
  `remark` varchar(50) DEFAULT NULL,
  `purchase_divide_order_id` bigint DEFAULT NULL,
  `purchase_amount` decimal(10,5) DEFAULT NULL,
  `material_specification` varchar(50) DEFAULT NULL,
  `color` varchar(40) DEFAULT NULL,
  `size_34_purchase_amount` int DEFAULT NULL,
  `size_35_purchase_amount` int DEFAULT NULL,
  `size_36_purchase_amount` int DEFAULT NULL,
  `size_37_purchase_amount` int DEFAULT NULL,
  `size_38_purchase_amount` int DEFAULT NULL,
  `size_39_purchase_amount` int DEFAULT NULL,
  `size_40_purchase_amount` int DEFAULT NULL,
  `size_41_purchase_amount` int DEFAULT NULL,
  `size_42_purchase_amount` int DEFAULT NULL,
  `size_43_purchase_amount` int DEFAULT NULL,
  `size_44_purchase_amount` int DEFAULT NULL,
  `size_45_purchase_amount` int DEFAULT NULL,
  `size_46_purchase_amount` int DEFAULT NULL,
  `size_type` char(1) NOT NULL DEFAULT (_utf8mb4'E'),
  `material_model` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`assets_purchase_order_item_id`),
  KEY `fk_assets_purchase_order_item` (`material_id`),
  KEY `fk_assets_purchase_order_item0` (`purchase_divide_order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assets_purchase_order_item`
--

LOCK TABLES `assets_purchase_order_item` WRITE;
/*!40000 ALTER TABLE `assets_purchase_order_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `assets_purchase_order_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `batch_info_type`
--

DROP TABLE IF EXISTS `batch_info_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `batch_info_type` (
  `batch_info_type_id` int NOT NULL AUTO_INCREMENT,
  `batch_info_type_name` varchar(10) DEFAULT NULL,
  `size_34_name` varchar(5) DEFAULT NULL,
  `size_35_name` varchar(5) DEFAULT NULL,
  `size_36_name` varchar(5) DEFAULT NULL,
  `size_37_name` varchar(5) DEFAULT NULL,
  `size_38_name` varchar(5) DEFAULT NULL,
  `size_39_name` varchar(5) DEFAULT NULL,
  `size_40_name` varchar(5) DEFAULT NULL,
  `size_41_name` varchar(5) DEFAULT NULL,
  `size_42_name` varchar(5) DEFAULT NULL,
  `size_43_name` varchar(5) DEFAULT NULL,
  `size_44_name` varchar(5) DEFAULT NULL,
  `size_45_name` varchar(5) DEFAULT NULL,
  `size_46_name` varchar(5) DEFAULT NULL,
  PRIMARY KEY (`batch_info_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `batch_info_type`
--

LOCK TABLES `batch_info_type` WRITE;
/*!40000 ALTER TABLE `batch_info_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `batch_info_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bom`
--

DROP TABLE IF EXISTS `bom`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bom` (
  `bom_id` bigint NOT NULL AUTO_INCREMENT,
  `bom_rid` varchar(80) NOT NULL,
  `bom_type` tinyint NOT NULL,
  `order_shoe_type_id` bigint NOT NULL,
  `bom_status` char(1) DEFAULT '1',
  `total_bom_id` bigint DEFAULT NULL,
  PRIMARY KEY (`bom_id`),
  KEY `fk_boms_order_shoes` (`order_shoe_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bom`
--

LOCK TABLES `bom` WRITE;
/*!40000 ALTER TABLE `bom` DISABLE KEYS */;
/*!40000 ALTER TABLE `bom` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bom_item`
--

DROP TABLE IF EXISTS `bom_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bom_item` (
  `bom_item_id` bigint NOT NULL AUTO_INCREMENT,
  `material_id` bigint NOT NULL,
  `unit_usage` decimal(10,5) DEFAULT NULL,
  `total_usage` decimal(10,5) NOT NULL,
  `department_id` int DEFAULT NULL,
  `remark` varchar(100) DEFAULT NULL,
  `bom_id` bigint NOT NULL,
  `material_specification` varchar(40) DEFAULT NULL,
  `bom_item_add_type` char(1) NOT NULL DEFAULT '0',
  `bom_item_color` varchar(40) DEFAULT NULL,
  `size_34_total_usage` int DEFAULT NULL,
  `size_35_total_usage` int DEFAULT NULL,
  `size_36_total_usage` int DEFAULT NULL,
  `size_37_total_usage` int DEFAULT NULL,
  `size_38_total_usage` int DEFAULT NULL,
  `size_39_total_usage` int DEFAULT NULL,
  `size_40_total_usage` int DEFAULT NULL,
  `size_41_total_usage` int DEFAULT NULL,
  `size_42_total_usage` int DEFAULT NULL,
  `size_43_total_usage` int DEFAULT NULL,
  `size_44_total_usage` int DEFAULT NULL,
  `size_45_total_usage` int DEFAULT NULL,
  `size_46_total_usage` int DEFAULT NULL,
  `size_type` char(1) DEFAULT 'E',
  `material_model` varchar(40) DEFAULT NULL,
  `material_second_type` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`bom_item_id`),
  KEY `fk_bom_items_departments` (`department_id`),
  KEY `fk_bom_items_materials` (`material_id`),
  KEY `fk_bom_items_boms` (`bom_id`),
  KEY `fk_bom_item_color` (`bom_item_color`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bom_item`
--

LOCK TABLES `bom_item` WRITE;
/*!40000 ALTER TABLE `bom_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `bom_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `character`
--

DROP TABLE IF EXISTS `character`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `character` (
  `character_id` int NOT NULL AUTO_INCREMENT,
  `character_name` varchar(40) NOT NULL,
  PRIMARY KEY (`character_id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `character`
--

LOCK TABLES `character` WRITE;
/*!40000 ALTER TABLE `character` DISABLE KEYS */;
INSERT INTO `character` VALUES (1,'超级管理员'),(2,'董事长/总经理'),(3,'生产副总'),(4,'业务部经理'),(5,'技术部经理'),(6,'生产部经理'),(7,'开发部经理'),(8,'总仓经理'),(9,'物控部经理'),(10,'财务部经理'),(11,'裁断主任'),(12,'针车主任'),(13,'成型主任'),(14,'人事部经理'),(15,'行政部经理'),(16,'品质部经理'),(17,'技术文员'),(18,'用量计算'),(19,'半成品仓管理员'),(20,'成品仓管理员'),(21,'业务部文员');
/*!40000 ALTER TABLE `character` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `color`
--

DROP TABLE IF EXISTS `color`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `color` (
  `color_id` int NOT NULL AUTO_INCREMENT,
  `color_name` varchar(30) NOT NULL,
  `color_en_name` varchar(50) DEFAULT NULL,
  `color_sp_name` varchar(50) DEFAULT NULL,
  `color_it_name` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`color_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `color`
--

LOCK TABLES `color` WRITE;
/*!40000 ALTER TABLE `color` DISABLE KEYS */;
/*!40000 ALTER TABLE `color` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customer`
--

DROP TABLE IF EXISTS `customer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer` (
  `customer_id` int NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(50) NOT NULL,
  `customer_brand` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer`
--

LOCK TABLES `customer` WRITE;
/*!40000 ALTER TABLE `customer` DISABLE KEYS */;
/*!40000 ALTER TABLE `customer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `default_bom`
--

DROP TABLE IF EXISTS `default_bom`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `default_bom` (
  `default_bom_id` bigint NOT NULL AUTO_INCREMENT,
  `bom_rid` varchar(80) NOT NULL,
  `bom_type` tinyint NOT NULL,
  `shoe_id` int NOT NULL,
  `bom_status` char(1) DEFAULT (_utf8mb4'1'),
  PRIMARY KEY (`default_bom_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `default_bom`
--

LOCK TABLES `default_bom` WRITE;
/*!40000 ALTER TABLE `default_bom` DISABLE KEYS */;
/*!40000 ALTER TABLE `default_bom` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `default_bom_item`
--

DROP TABLE IF EXISTS `default_bom_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `default_bom_item` (
  `default_bom_item_id` bigint NOT NULL AUTO_INCREMENT,
  `material_id` bigint NOT NULL,
  `department_id` int DEFAULT NULL,
  `remark` varchar(100) DEFAULT NULL,
  `material_specification` varchar(40) DEFAULT NULL,
  `bom_item_color` varchar(40) DEFAULT NULL,
  `material_model` varchar(40) DEFAULT NULL,
  `default_bom_id` bigint NOT NULL,
  PRIMARY KEY (`default_bom_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `default_bom_item`
--

LOCK TABLES `default_bom_item` WRITE;
/*!40000 ALTER TABLE `default_bom_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `default_bom_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `department`
--

DROP TABLE IF EXISTS `department`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `department` (
  `department_id` int NOT NULL AUTO_INCREMENT,
  `department_name` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`department_id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `department`
--

LOCK TABLES `department` WRITE;
/*!40000 ALTER TABLE `department` DISABLE KEYS */;
INSERT INTO `department` VALUES (1,'裁断工段'),(2,'针车工段'),(3,'成型工段'),(4,'生产部'),(5,'技术部'),(6,'物控部'),(7,'行政部'),(8,'总经理'),(9,'人事部'),(10,'业务部'),(11,'开发部'),(12,'总仓'),(13,'财务部');
/*!40000 ALTER TABLE `department` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `event`
--

DROP TABLE IF EXISTS `event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `event` (
  `event_id` int NOT NULL AUTO_INCREMENT,
  `staff_id` int NOT NULL,
  `handle_time` datetime NOT NULL,
  `operation_id` int NOT NULL,
  `event_order_id` bigint DEFAULT NULL,
  `event_order_shoe_id` bigint DEFAULT NULL,
  `event_type` tinyint DEFAULT '0',
  PRIMARY KEY (`event_id`),
  KEY `fk_events_staffs` (`staff_id`),
  KEY `fk_events_operations` (`operation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event`
--

LOCK TABLES `event` WRITE;
/*!40000 ALTER TABLE `event` DISABLE KEYS */;
/*!40000 ALTER TABLE `event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `finished_shoe_storage`
--

DROP TABLE IF EXISTS `finished_shoe_storage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `finished_shoe_storage` (
  `finished_shoe_id` bigint NOT NULL AUTO_INCREMENT,
  `finished_inbound_datetime` datetime DEFAULT NULL,
  `order_shoe_type_id` bigint NOT NULL,
  `finished_amount` int NOT NULL DEFAULT '0',
  `finished_status` tinyint DEFAULT NULL COMMENT '0：未入库\n1：已入库\n2：已出库',
  `current_revenue` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`finished_shoe_id`),
  KEY `fk_finished_shoe_storage` (`order_shoe_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `finished_shoe_storage`
--

LOCK TABLES `finished_shoe_storage` WRITE;
/*!40000 ALTER TABLE `finished_shoe_storage` DISABLE KEYS */;
/*!40000 ALTER TABLE `finished_shoe_storage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inbound_record`
--

DROP TABLE IF EXISTS `inbound_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inbound_record` (
  `inbound_record_id` bigint NOT NULL AUTO_INCREMENT,
  `inbound_rid` varchar(50) DEFAULT NULL,
  `inbound_amount` decimal(10,5) DEFAULT NULL,
  `size_34_inbound_amount` int DEFAULT NULL,
  `size_35_inbound_amount` int DEFAULT NULL,
  `size_36_inbound_amount` int DEFAULT NULL,
  `size_37_inbound_amount` int DEFAULT NULL,
  `size_38_inbound_amount` int DEFAULT NULL,
  `size_39_inbound_amount` int DEFAULT NULL,
  `size_40_inbound_amount` int DEFAULT NULL,
  `size_41_inbound_amount` int DEFAULT NULL,
  `size_42_inbound_amount` int DEFAULT NULL,
  `size_43_inbound_amount` int DEFAULT NULL,
  `size_44_inbound_amount` int DEFAULT NULL,
  `size_45_inbound_amount` int DEFAULT NULL,
  `size_46_inbound_amount` int DEFAULT NULL,
  `inbound_datetime` datetime NOT NULL,
  `inbound_type` tinyint NOT NULL COMMENT '0：采购入库\n1：生产剩余',
  `material_storage_id` bigint DEFAULT NULL,
  `size_material_storage_id` bigint DEFAULT NULL,
  PRIMARY KEY (`inbound_record_id`),
  KEY `fk_instock_record` (`material_storage_id`),
  KEY `fk_instock_record0` (`size_material_storage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inbound_record`
--

LOCK TABLES `inbound_record` WRITE;
/*!40000 ALTER TABLE `inbound_record` DISABLE KEYS */;
/*!40000 ALTER TABLE `inbound_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `material`
--

DROP TABLE IF EXISTS `material`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `material` (
  `material_id` bigint NOT NULL AUTO_INCREMENT,
  `material_name` varchar(60) NOT NULL,
  `material_unit` varchar(4) DEFAULT NULL,
  `material_creation_date` date DEFAULT NULL,
  `material_supplier` int NOT NULL,
  `material_type_id` bigint NOT NULL DEFAULT '1',
  `material_category` int DEFAULT '0',
  PRIMARY KEY (`material_id`)
) ENGINE=InnoDB AUTO_INCREMENT=323 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `material`
--

LOCK TABLES `material` WRITE;
/*!40000 ALTER TABLE `material` DISABLE KEYS */;
INSERT INTO `material` VALUES (1,'采购革','米','2024-09-07',1,1,0),(2,'真皮','米','2024-09-07',1,1,0),(3,'羊筋绒','米','2024-09-07',1,1,0),(4,'瑞佳','米','2024-09-07',30,1,0),(5,'宝社','米','2024-09-07',31,1,0),(6,'鸿运','米','2024-09-07',207,1,0),(7,'润丰','米','2024-09-07',59,1,0),(8,'鸿源','米','2024-09-07',63,1,0),(9,'真皮绒','米','2024-09-07',1,1,0),(10,'唯佳','米','2024-09-07',62,1,0),(11,'国茂','米','2024-09-07',70,1,0),(12,'深源','米','2024-09-07',81,1,0),(13,'添鸿','米','2024-09-07',83,1,0),(14,'瓯瑞','米','2024-09-07',86,1,0),(15,'贴皮','米','2024-09-07',1,1,0),(16,'PU里','米','2024-09-07',1,2,0),(17,'几皮里','米','2024-09-07',1,2,0),(18,'布里','米','2024-09-07',1,2,0),(19,'毛里','米','2024-09-07',1,2,0),(20,'拉毛布','米','2024-09-07',1,2,0),(21,'定型布','米','2024-09-07',1,2,0),(22,'鞋眼衬','米','2024-09-07',1,2,0),(23,'海绵-张','张','2024-09-07',1,2,0),(24,'海绵-米','米','2024-09-07',1,2,0),(25,'猪皮里','尺','2024-09-07',1,2,0),(26,'乳胶-件','件','2024-09-07',1,2,0),(27,'PE纸','件','2024-09-07',1,2,0),(28,'海绵条','条','2024-09-07',1,2,0),(29,'内衬','米','2024-09-07',1,2,0),(30,'乳胶-米','米','2024-09-07',1,2,0),(31,'高丽棉-米','米','2024-09-07',1,2,0),(32,'上线','个','2024-09-07',1,3,0),(33,'下线','个','2024-09-07',1,3,0),(34,'蜡线','斤','2024-09-07',1,3,0),(35,'空心线','个','2024-09-07',1,3,0),(36,'双面胶','件','2024-09-07',1,3,0),(37,'美纹纸','件','2024-09-07',1,3,0),(38,'编织袋','条','2024-09-07',1,3,0),(39,'保险丝','个','2024-09-07',1,3,0),(40,'压缝条','盘','2024-09-07',1,3,0),(41,'补强带','件','2024-09-07',1,3,0),(42,'保险条','盘','2024-09-07',1,3,0),(43,'牛皮纸','件','2024-09-07',1,3,0),(44,'珠光线','个','2024-09-07',1,3,0),(45,'胶水','公斤','2024-09-07',1,4,0),(46,'处理剂','公斤','2024-09-07',1,4,0),(47,'固化剂','瓶','2024-09-07',1,4,0),(48,'鞋面油漆','公斤','2024-09-07',1,4,0),(49,'鞋面蜡水','公斤','2024-09-07',1,4,0),(50,'清洁剂','公斤','2024-09-07',1,4,0),(51,'改色剂','公斤','2024-09-07',1,4,0),(52,'巴西蜡','块','2024-09-07',1,4,0),(53,'粉胶-桶','桶','2024-09-07',1,4,0),(54,'喷胶','公斤','2024-09-07',1,4,0),(55,'黑膏','瓶','2024-09-07',1,4,0),(56,'白胶','公斤','2024-09-07',1,4,0),(57,'去胶剂','公斤','2024-09-07',1,4,0),(58,'处理剂-壶','壶','2024-09-07',1,4,0),(59,'鞋油','公斤','2024-09-07',1,4,0),(60,'硫化剂','瓶','2024-09-07',1,4,0),(61,'补伤膏','公斤','2024-09-07',1,4,0),(62,'烧焦蜡','块','2024-09-07',1,4,0),(63,'鞋面蜡油','公斤','2024-09-07',1,4,0),(64,'包头水','公斤','2024-09-07',1,4,0),(65,'渗透剂','瓶','2024-09-07',1,4,0),(66,'填充蜡','块','2024-09-07',1,4,0),(67,'雾蜡剂','公斤','2024-09-07',1,4,0),(68,'擦色蜡','块','2024-09-07',1,4,0),(69,'皮胚浓缩蜡液','公斤','2024-09-07',1,4,0),(70,'抛光蜡','条','2024-09-07',1,4,0),(71,'处理剂-瓶','瓶','2024-09-07',1,4,0),(72,'修补膏','公斤','2024-09-07',1,4,0),(73,'封口胶','瓶','2024-09-07',1,4,0),(74,'饰扣-双','双','2024-09-07',1,5,0),(75,'饰扣-套','套','2024-09-07',1,5,0),(76,'小饰扣-斤','斤','2024-09-07',1,5,0),(77,'小饰扣-包','包','2024-09-07',1,5,0),(78,'鞋眼-斤','斤','2024-09-07',1,5,0),(79,'鞋眼-包/万','包','2024-09-07',1,5,0),(80,'鞋眼垫片-斤','斤','2024-09-07',1,5,0),(81,'帽钉-斤','斤','2024-09-07',1,5,0),(82,'帽钉-包','包','2024-09-07',1,5,0),(83,'尼龙拉链-双','双','2024-09-07',1,5,0),(84,'尼龙拉链-条','条','2024-09-07',1,5,0),(85,'金属拉链-双','双','2024-09-07',1,5,0),(86,'金属拉链-条','条','2024-09-07',1,5,0),(87,'拉链头-双','双','2024-09-07',1,5,0),(88,'拉链头-个','个','2024-09-07',1,5,0),(89,'鞋带-双','双','2024-09-07',1,5,0),(90,'松紧-米','米','2024-09-07',1,5,0),(91,'松紧-盘','盘','2024-09-07',1,5,0),(92,'织带-米','米','2024-09-07',1,5,0),(93,'织带-盘','盘','2024-09-07',1,5,0),(94,'毛刺-米','米','2024-09-07',1,5,0),(95,'毛刺-盘','盘','2024-09-07',1,5,0),(96,'皮标','双','2024-09-07',1,5,0),(97,'布标','双','2024-09-07',1,5,0),(98,'鞋眼-套','套','2024-09-07',1,5,0),(99,'帽钉-颗','颗','2024-09-07',1,5,0),(100,'布标-片','张','2024-09-07',1,5,0),(101,'鞋眼垫片-颗','颗','2024-09-07',1,5,0),(102,'穿花条','米','2024-09-07',1,5,0),(103,'鞋盒','个','2024-09-07',1,6,0),(104,'隔板','张','2024-09-07',1,6,0),(105,'脚模','双','2024-09-07',1,6,0),(106,'泡沫筒衬','双','2024-09-07',1,6,0),(107,'纸筒衬','双','2024-09-07',1,6,0),(108,'鞋盒加工','个','2024-09-07',1,6,0),(109,'双面玖龙双瓦外箱','个','2024-09-07',1,6,0),(110,'海王B级双瓦外箱','个','2024-09-07',1,6,0),(111,'拷贝纸','张','2024-09-07',1,6,0),(112,'塞纸','件','2024-09-07',1,6,0),(113,'贴标','套','2024-09-07',1,6,0),(114,'包装袋','双','2024-09-07',1,6,0),(115,'防霉片','张','2024-09-07',1,6,0),(116,'胶带纸','卷','2024-09-07',1,6,0),(117,'铜板纸','卷','2024-09-07',1,6,0),(118,'碳带','卷','2024-09-07',1,6,0),(119,'吊牌','个','2024-09-07',1,6,0),(120,'B级双瓦外箱','个','2024-09-07',1,6,0),(121,'干燥剂','包','2024-09-07',1,6,0),(122,'特一双瓦外箱','个','2024-09-07',1,6,0),(123,'白板双瓦外箱','个','2024-09-07',1,6,0),(124,'B级单瓦外箱','个','2024-09-07',1,6,0),(125,'纸筒管','个','2024-09-07',1,6,0),(126,'防霉纸','张','2024-09-07',1,6,0),(127,'海王B级双瓦垫片','个','2024-09-07',1,6,0),(128,'B级单瓦垫片','个','2024-09-07',1,6,0),(129,'B级双瓦垫片','个','2024-09-07',1,6,0),(130,'特殊白板双瓦外箱','个','2024-09-07',1,6,0),(131,'泡沫棒','双','2024-09-07',1,6,0),(132,'双瓦垫片','个','2024-09-07',1,6,0),(133,'美牛双瓦外箱','个','2024-09-07',1,6,0),(134,'打包带','卷','2024-09-07',1,6,0),(135,'纸衬','双','2024-09-07',1,6,0),(136,'美牛双瓦垫片','个','2024-09-07',1,6,0),(137,'小帆船外箱','个','2024-09-07',1,6,0),(138,'大底','双','2024-09-07',1,7,1),(139,'中底','双','2024-09-07',1,7,1),(140,'鞋跟','双','2024-09-07',1,7,0),(141,'底片','双','2024-09-07',1,7,0),(142,'出面','双','2024-09-07',1,7,0),(143,'内增高','双','2024-09-07',1,7,0),(144,'中底板','张','2024-09-07',1,7,0),(145,'防水台','张','2024-09-07',1,7,0),(146,'中底卡纸','双','2024-09-07',1,7,0),(147,'其他工具','件','2024-09-07',1,8,0),(148,'剪刀','把','2024-09-07',1,8,0),(149,'手套','件','2024-09-07',1,8,0),(150,'刷子','把','2024-09-07',1,8,0),(151,'口罩','件','2024-09-07',1,8,0),(152,'针筒','件','2024-09-07',1,8,0),(153,'白碎布','斤','2024-09-07',1,8,0),(154,'背心袋','件','2024-09-07',1,8,0),(155,'尼龙绳','斤','2024-09-07',1,8,0),(156,'橡皮筋','斤','2024-09-07',1,8,0),(157,'擦胶皮','件','2024-09-07',1,8,0),(158,'胶油壶','个','2024-09-07',1,8,0),(159,'记号笔','件','2024-09-07',1,8,0),(160,'砂轮纸','件','2024-09-07',1,8,0),(161,'清洗笔','件','2024-09-07',1,8,0),(162,'707胶','件','2024-09-07',1,8,0),(163,'装跟钉','件','2024-09-07',1,8,0),(164,'垫芯','件','2024-09-07',1,8,0),(165,'复0.6切片','米','2024-09-07',1,9,0),(166,'复0.6棕白切片','米','2024-09-07',1,9,0),(167,'复0.8切片','米','2024-09-07',1,9,0),(168,'复0.8棕白切片','米','2024-09-07',1,9,0),(169,'复1.0切片','米','2024-09-07',1,9,0),(170,'复1.0棕白切片','米','2024-09-07',1,9,0),(171,'复1.1切片','米','2024-09-07',1,9,0),(172,'复1.1棕白切片','米','2024-09-07',1,9,0),(173,'复1.2切片','米','2024-09-07',1,9,0),(174,'复1.2棕白切片','米','2024-09-07',1,9,0),(175,'复1.5切片','米','2024-09-07',1,9,0),(176,'复1.5棕白切片','米','2024-09-07',1,9,0),(177,'复2*1布','米','2024-09-07',1,9,0),(178,'复2*3布','米','2024-09-07',1,9,0),(179,'复PU里','米','2024-09-07',1,9,0),(180,'复几皮里','米','2024-09-07',1,9,0),(181,'复超纤里','米','2024-09-07',1,9,0),(182,'复佳积布','米','2024-09-07',1,9,0),(183,'复定型布','米','2024-09-07',1,9,0),(184,'复0.2海绵+里子布','米','2024-09-07',1,9,0),(185,'复0.3海绵+里子布','米','2024-09-07',1,9,0),(186,'复0.4海绵+里子布','米','2024-09-07',1,9,0),(187,'复2.0回力胶','米','2024-09-07',1,9,0),(188,'复3.0回力胶','米','2024-09-07',1,9,0),(189,'复3.0乳胶','米','2024-09-07',1,9,0),(190,'对复','米','2024-09-07',1,9,0),(191,'两边细布中间+PE纸','米','2024-09-07',1,9,0),(192,'上胶+PE纸','米','2024-09-07',1,9,0),(193,'复细布','米','2024-09-07',1,9,0),(194,'复无纺布','米','2024-09-07',1,9,0),(195,'复1.0切片+1.0膜+定型布','米','2024-09-07',1,9,0),(196,'复2*3布上胶+PE纸','米','2024-09-07',1,9,0),(197,'复1.0切片+定型布','米','2024-09-07',1,9,0),(198,'复3.0记忆海绵+2.0乳胶','米','2024-09-07',1,9,0),(199,'复0.6切片+PU里','米','2024-09-07',1,9,0),(200,'复5.0记忆海绵+无纺布','米','2024-09-07',1,9,0),(201,'复细布+2*3布','米','2024-09-07',1,9,0),(202,'复8N布','米','2024-09-07',1,9,0),(203,'复无纺布+3.0回力胶','米','2024-09-07',1,9,0),(204,'复2*3布+定型布','米','2024-09-07',1,9,0),(205,'复2*1布+2*3布','米','2024-09-07',1,9,0),(206,'复0.6切片+PE纸','米','2024-09-07',1,9,0),(207,'复细布+1.5切片','米','2024-09-07',1,9,0),(208,'复佳积布+2*3布','米','2024-09-07',1,9,0),(209,'复18磅布上防脱纱','米','2024-09-07',1,9,0),(210,'复1.2切片+定型布','米','2024-09-07',1,9,0),(211,'复细布+2*3布*定型布','米','2024-09-07',1,9,0),(212,'复0.3海绵','米','2024-09-07',1,9,0),(213,'复拉毛布上胶+PE纸','米','2024-09-07',1,9,0),(214,'复无纺布上胶+PE纸','米','2024-09-07',1,9,0),(215,'复1.0切片+PU里','米','2024-09-07',1,9,0),(216,'复14磅布','米','2024-09-07',1,9,0),(217,'复佳积布+2*1布','米','2024-09-07',1,9,0),(218,'复佳积布上胶+PE纸','米','2024-09-07',1,9,0),(219,'复2*3布+PU里','米','2024-09-07',1,9,0),(220,'复18磅布+2*1布','米','2024-09-07',1,9,0),(221,'复拉毛布','米','2024-09-07',1,9,0),(222,'复无纺布+羊筋绒','米','2024-09-07',1,9,0),(223,'复佳积布+1.2切片','米','2024-09-07',1,9,0),(224,'复1.0切片+1.0膜+定型布复PU里','米','2024-09-07',1,9,0),(225,'复细布+1.2切片','米','2024-09-07',1,9,0),(226,'复0.8切片加网','米','2024-09-07',1,9,0),(227,'复0.5海绵','米','2024-09-07',1,9,0),(228,'复细布+1.0切片','米','2024-09-07',1,9,0),(229,'复1.2切片+1.0膜+定型布','米','2024-09-07',1,9,0),(230,'复细布+2*3布+PU里','米','2024-09-07',1,9,0),(231,'复0.3海绵+无纺布','米','2024-09-07',1,9,0),(232,'复2*1布+2*3布+定型布','米','2024-09-07',1,9,0),(233,'复0.5海绵+3.0回力胶+特克松','米','2024-09-07',1,9,0),(234,'复0.5海绵+里子布','米','2024-09-07',1,9,0),(235,'复里子布','米','2024-09-07',1,9,0),(236,'复3.0高力棉','米','2024-09-07',1,9,0),(237,'复5.5大力棉+1.0EVA','米','2024-09-07',1,9,0),(238,'复2*1布+2*3布+超纤布','米','2024-09-07',1,9,0),(239,'复2*1布上胶+PE纸','米','2024-09-07',1,9,0),(240,'复0.5海绵+无纺布','米','2024-09-07',1,9,0),(241,'复2*1布+2*3布+帆布','米','2024-09-07',1,9,0),(242,'复1.0切片上胶+PE纸','米','2024-09-07',1,9,0),(243,'复佳积布+无纺布','米','2024-09-07',1,9,0),(244,'复3.0记忆海绵','米','2024-09-07',1,9,0),(245,'复无纺布+PU里','米','2024-09-07',1,9,0),(246,'复2*3布+无纺布','米','2024-09-07',1,9,0),(247,'复2*3布+细布','米','2024-09-07',1,9,0),(248,'复细布+佳积布','米','2024-09-07',1,9,0),(249,'复2*3布+超纤布','米','2024-09-07',1,9,0),(250,'复细布+2*3布+超纤布','米','2024-09-07',1,9,0),(251,'复0.6海绵+无纺布','米','2024-09-07',1,9,0),(252,'复空心棉','米','2024-09-07',1,9,0),(253,'复2*3布+拉毛布','米','2024-09-07',1,9,0),(254,'复4.0乳胶','米','2024-09-07',1,9,0),(255,'复佳积布+0.3海绵+里子布','米','2024-09-07',1,9,0),(256,'复无纺布+3.0高力棉','米','2024-09-07',1,9,0),(257,'复佳积布+0.2海绵+里子布','米','2024-09-07',1,9,0),(258,'复0.8EVA','米','2024-09-07',1,9,0),(259,'复无纺布+高力棉','米','2024-09-07',1,9,0),(260,'复高力棉','米','2024-09-07',1,9,0),(261,'复2*1布+定型布','米','2024-09-07',1,9,0),(262,'复2*1布+2*3布+无纺布','米','2024-09-07',1,9,0),(263,'复防爆胶','米','2024-09-07',1,9,0),(264,'复4*3布+无纺布','米','2024-09-07',1,9,0),(265,'复无纺布+0.5海绵+无纺布','米','2024-09-07',1,9,0),(266,'复细布+1.2切片+PU里','米','2024-09-07',1,9,0),(267,'复2*1布+无纺布','米','2024-09-07',1,9,0),(268,'复2*3布+定型布+无纺布','米','2024-09-07',1,9,0),(269,'复2*3布+膜+定型布复PU里','米','2024-09-07',1,9,0),(270,'复4*3布','米','2024-09-07',1,9,0),(271,'复5.0记忆海绵','米','2024-09-07',1,9,0),(272,'复1.5SBR+里子布','米','2024-09-07',1,9,0),(273,'复细布上胶+PE纸','米','2024-09-07',1,9,0),(274,'0.8切片复细布上胶+PE纸','米','2024-09-07',1,9,0),(275,'加工费-米','双','2024-09-07',1,10,0),(276,'加工费-双','双','2024-09-07',1,10,0),(277,'加工费-件','双','2024-09-07',1,10,0),(278,'加工费-盘','双','2024-09-07',1,10,0),(279,'加工费-次','双','2024-09-07',1,10,0),(280,'成型烫加工','双','2024-09-07',1,10,0),(281,'全烫加工','双','2024-09-07',1,10,0),(282,'热熔胶-双','双','2024-09-07',1,10,0),(283,'飞织加工','双','2024-09-07',1,10,0),(284,'刀模-支','双','2024-09-07',1,10,0),(285,'刀模-套','双','2024-09-07',1,10,0),(286,'男单','双','2024-09-07',1,11,0),(287,'男棉','双','2024-09-07',1,11,0),(288,'男高棉','双','2024-09-07',1,11,0),(289,'女单','双','2024-09-07',1,11,0),(290,'女棉','双','2024-09-07',1,11,0),(291,'女高棉','双','2024-09-07',1,11,0),(292,'楦头加工','双','2024-09-07',1,11,0),(293,'女二棉','双','2024-09-07',1,11,0),(294,'男二棉','双','2024-09-07',1,11,0),(295,'男单棉','双','2024-09-07',1,11,0),(296,'维修费','次','2024-09-07',1,12,0),(297,'零配件','件','2024-09-07',1,12,0),(298,'机器设备','件','2024-09-07',1,12,0),(299,'办公设备','件','2024-09-07',1,12,0),(300,'洗洁精','斤','2024-09-07',1,12,0),(301,'后勤用品','件','2024-09-07',1,12,0),(302,'柴油','斤','2024-09-07',1,12,0),(303,'办公用品','件','2024-09-07',1,12,0),(304,'医疗用品','件','2024-09-07',1,12,0),(305,'液压油','桶','2024-09-07',1,12,0),(306,'开发样品','件','2024-09-07',1,13,0),(307,'样品-米','米','2024-09-07',1,13,0),(308,'样品-件','件','2024-09-07',1,13,0),(309,'样品-套','套','2024-09-07',1,13,0),(310,'开发工具','件','2024-09-07',1,13,0),(311,'样品皮-尺','尺','2024-09-07',1,13,0),(312,'样品-双','双','2024-09-07',1,13,0),(313,'莱卡布','米','2024-11-01',36,1,0),(314,'弹力布','米','2024-11-01',1,2,0),(315,'网布','米','2024-11-01',1,2,0),(316,'PU里','米','2024-11-01',29,2,0),(317,'中底','双','2024-11-01',208,7,0),(318,'大底','对','2024-11-06',33,7,1),(319,'嘉泰','米','2024-11-06',29,2,0),(320,'佳织布','米','2024-11-06',1,2,0),(321,'森达','个','2024-11-06',6,12,1),(322,'中底','对','2024-11-06',130,7,1);
/*!40000 ALTER TABLE `material` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `material_storage`
--

DROP TABLE IF EXISTS `material_storage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `material_storage` (
  `material_storage_id` bigint NOT NULL AUTO_INCREMENT,
  `order_shoe_id` bigint DEFAULT NULL,
  `material_id` bigint NOT NULL,
  `estimated_inbound_amount` decimal(10,5) DEFAULT '0.00000',
  `actual_inbound_amount` decimal(10,5) DEFAULT '0.00000',
  `current_amount` decimal(10,5) NOT NULL DEFAULT (0),
  `unit_price` decimal(10,2) DEFAULT NULL,
  `material_specification` varchar(40) DEFAULT NULL,
  `material_outsource_status` tinyint NOT NULL DEFAULT '0',
  `material_outsource_outbound_date` date DEFAULT NULL,
  `material_storage_color` varchar(40) DEFAULT NULL,
  `purchase_divide_order_id` bigint DEFAULT NULL,
  `material_estimated_arrival_date` date DEFAULT NULL,
  `material_model` varchar(40) DEFAULT NULL,
  `material_storage_status` tinyint DEFAULT (_utf8mb4'0') COMMENT '0：未完成入库\n1：已完成入库\n2：已完成出库',
  PRIMARY KEY (`material_storage_id`),
  KEY `fk_material_storage` (`order_shoe_id`),
  KEY `fk_material_storage_materials` (`material_id`),
  KEY `fk_material_storage_color` (`material_storage_color`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `material_storage`
--

LOCK TABLES `material_storage` WRITE;
/*!40000 ALTER TABLE `material_storage` DISABLE KEYS */;
/*!40000 ALTER TABLE `material_storage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `material_type`
--

DROP TABLE IF EXISTS `material_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `material_type` (
  `material_type_id` bigint NOT NULL AUTO_INCREMENT,
  `material_type_name` varchar(50) NOT NULL,
  `warehouse_id` int NOT NULL,
  PRIMARY KEY (`material_type_id`),
  KEY `fk_material_type` (`warehouse_id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `material_type`
--

LOCK TABLES `material_type` WRITE;
/*!40000 ALTER TABLE `material_type` DISABLE KEYS */;
INSERT INTO `material_type` VALUES (1,'面料',1),(2,'里料',2),(3,'辅料',3),(4,'化工',4),(5,'饰品',5),(6,'包材',6),(7,'底材',7),(8,'生产工具',8),(9,'复合',9),(10,'加工',10),(11,'刀模',11),(12,'楦头',12),(13,'办公后勤',13),(14,'开发样品',14),(15,'固定资产',15);
/*!40000 ALTER TABLE `material_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `material_warehouse`
--

DROP TABLE IF EXISTS `material_warehouse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `material_warehouse` (
  `material_warehouse_id` int NOT NULL AUTO_INCREMENT,
  `material_warehouse_name` varchar(20) NOT NULL,
  `material_warehouse_creation_date` date NOT NULL,
  PRIMARY KEY (`material_warehouse_id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `material_warehouse`
--

LOCK TABLES `material_warehouse` WRITE;
/*!40000 ALTER TABLE `material_warehouse` DISABLE KEYS */;
INSERT INTO `material_warehouse` VALUES (1,'面料仓','2024-09-07'),(2,'里料仓','2024-09-07'),(3,'辅料仓','2024-09-07'),(4,'化工仓','2024-09-07'),(5,'饰品仓','2024-09-07'),(6,'包材仓','2024-09-07'),(7,'底材仓','2024-09-07'),(8,'工具仓','2024-09-07'),(9,'复合仓','2024-09-07'),(10,'加工仓','2024-09-07'),(11,'刀模仓','2024-09-07'),(12,'楦头仓','2024-09-07'),(13,'办公后勤仓','2024-09-07'),(14,'开发部仓','2024-09-07'),(15,'固定资产仓','2024-09-07');
/*!40000 ALTER TABLE `material_warehouse` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operation`
--

DROP TABLE IF EXISTS `operation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operation` (
  `operation_id` int NOT NULL,
  `operation_name` varchar(40) NOT NULL,
  `operation_type` tinyint NOT NULL DEFAULT (_utf8mb4'0') COMMENT '0 无相关\n1 order流程\n2 order_shoe流程',
  `operation_modified_status` int DEFAULT NULL,
  `operation_modified_value` int DEFAULT NULL,
  PRIMARY KEY (`operation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operation`
--

LOCK TABLES `operation` WRITE;
/*!40000 ALTER TABLE `operation` DISABLE KEYS */;
INSERT INTO `operation` VALUES (0,'Type-1-test-0',1,0,1),(1,'Type-1-test-1',1,0,2),(2,'Type-1-test-2',1,1,1),(3,'Type-1-test-3',1,1,2),(4,'Type-1-test-4',1,2,1),(5,'Type-1-test-5',1,2,2),(6,'Type-1-test-6',1,3,1),(7,'Type-1-test-7',1,3,2),(8,'Type-1-test-8',1,4,1),(9,'Type-1-test-9',1,4,2),(10,'Type-1-test-10',1,5,1),(11,'Type-1-test-11',1,5,2),(12,'Type-1-test-12',1,6,1),(13,'Type-1-test-13',1,6,2),(14,'Type-1-test-14',1,7,1),(15,'Type-1-test-15',1,7,2),(16,'Type-1-test-16',1,8,1),(17,'Type-1-test-17',1,8,2),(18,'Type-1-test-18',1,9,1),(19,'Type-1-test-19',1,9,2),(20,'Type-1-test-20',1,10,1),(21,'Type-1-test-21',1,10,2),(22,'Type-1-test-22',1,11,1),(23,'Type-1-test-23',1,11,2),(24,'Type-1-test-24',1,12,1),(25,'Type-1-test-25',1,12,2),(26,'Type-1-test-26',1,13,1),(27,'Type-1-test-27',1,13,2),(28,'Type-1-test-28',1,14,1),(29,'Type-1-test-29',1,14,2),(30,'Type-1-test-30',1,15,1),(31,'Type-1-test-31',1,15,2),(32,'Type-1-test-32',1,16,1),(33,'Type-1-test-33',1,16,2),(34,'Type-1-test-34',1,17,1),(35,'Type-1-test-35',1,17,2),(36,'Type-1-test-36',1,18,1),(37,'Type-1-test-37',1,18,2),(38,'Type-2-test-0',2,0,1),(39,'Type-2-test-1',2,0,2),(40,'Type-2-test-2',2,1,1),(41,'Type-2-test-3',2,1,2),(42,'Type-2-test-4',2,2,1),(43,'Type-2-test-5',2,2,2),(44,'Type-2-test-6',2,3,1),(45,'Type-2-test-7',2,3,2),(46,'Type-2-test-8',2,4,1),(47,'Type-2-test-9',2,4,2),(48,'Type-2-test-10',2,5,1),(49,'Type-2-test-11',2,5,2),(50,'Type-2-test-12',2,6,1),(51,'Type-2-test-13',2,6,2),(52,'Type-2-test-14',2,7,1),(53,'Type-2-test-15',2,7,2),(54,'Type-2-test-16',2,8,1),(55,'Type-2-test-17',2,8,2),(56,'Type-2-test-18',2,9,1),(57,'Type-2-test-19',2,9,2),(58,'Type-2-test-20',2,10,1),(59,'Type-2-test-21',2,10,2),(60,'Type-2-test-22',2,11,1),(61,'Type-2-test-23',2,11,2),(62,'Type-2-test-24',2,12,1),(63,'Type-2-test-25',2,12,2),(64,'Type-2-test-26',2,13,1),(65,'Type-2-test-27',2,13,2),(66,'Type-2-test-28',2,14,1),(67,'Type-2-test-29',2,14,2),(68,'Type-2-test-30',2,15,1),(69,'Type-2-test-31',2,15,2),(70,'Type-2-test-32',2,16,1),(71,'Type-2-test-33',2,16,2),(72,'Type-2-test-34',2,17,1),(73,'Type-2-test-35',2,17,2),(74,'Type-2-test-36',2,18,1),(75,'Type-2-test-37',2,18,2),(76,'Type-2-test-38',2,19,1),(77,'Type-2-test-39',2,19,2),(78,'Type-2-test-40',2,20,1),(79,'Type-2-test-41',2,20,2),(80,'Type-2-test-42',2,21,1),(81,'Type-2-test-43',2,21,2),(82,'Type-2-test-44',2,22,1),(83,'Type-2-test-45',2,22,2),(84,'Type-2-test-46',2,23,1),(85,'Type-2-test-47',2,23,2),(86,'Type-2-test-48',2,24,1),(87,'Type-2-test-49',2,24,2),(88,'Type-2-test-50',2,25,1),(89,'Type-2-test-51',2,25,2),(90,'Type-2-test-52',2,26,1),(91,'Type-2-test-53',2,26,2),(92,'Type-2-test-54',2,27,1),(93,'Type-2-test-55',2,27,2),(94,'Type-2-test-56',2,28,1),(95,'Type-2-test-57',2,28,2),(96,'Type-2-test-58',2,29,1),(97,'Type-2-test-59',2,29,2),(98,'Type-2-test-60',2,30,1),(99,'Type-2-test-61',2,30,2),(100,'Type-2-test-62',2,31,1),(101,'Type-2-test-63',2,31,2),(102,'Type-2-test-64',2,32,1),(103,'Type-2-test-65',2,32,2),(104,'Type-2-test-66',2,33,1),(105,'Type-2-test-67',2,33,2),(106,'Type-2-test-68',2,34,1),(107,'Type-2-test-69',2,34,2),(108,'Type-2-test-70',2,35,1),(109,'Type-2-test-71',2,35,2),(110,'Type-2-test-72',2,36,1),(111,'Type-2-test-73',2,36,2),(112,'Type-2-test-74',2,37,1),(113,'Type-2-test-75',2,37,2),(114,'Type-2-test-76',2,38,1),(115,'Type-2-test-77',2,38,2),(116,'Type-2-test-78',2,39,1),(117,'Type-2-test-79',2,39,2),(118,'Type-2-test-80',2,40,1),(119,'Type-2-test-81',2,40,2),(120,'Type-2-test-82',2,41,1),(121,'Type-2-test-83',2,41,2),(122,'Type-2-test-84',2,42,1),(123,'Type-2-test-85',2,42,2);
/*!40000 ALTER TABLE `operation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order`
--

DROP TABLE IF EXISTS `order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order` (
  `order_id` bigint NOT NULL AUTO_INCREMENT,
  `order_rid` varchar(40) NOT NULL,
  `order_cid` varchar(40) DEFAULT NULL,
  `order_type` char(1) NOT NULL DEFAULT 'N',
  `batch_info_type_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `customer_id` int NOT NULL,
  `salesman` varchar(10) DEFAULT NULL,
  `production_list_upload_status` char(1) DEFAULT '0',
  `amount_list_upload_status` char(1) DEFAULT (0),
  PRIMARY KEY (`order_id`),
  UNIQUE KEY `order_rid_UNIQUE` (`order_rid`),
  KEY `fk_orders_customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order`
--

LOCK TABLES `order` WRITE;
/*!40000 ALTER TABLE `order` DISABLE KEYS */;
/*!40000 ALTER TABLE `order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_shoe`
--

DROP TABLE IF EXISTS `order_shoe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_shoe` (
  `order_shoe_id` bigint NOT NULL AUTO_INCREMENT,
  `adjust_staff` varchar(20) DEFAULT NULL,
  `process_sheet_upload_status` char(1) DEFAULT NULL,
  `production_order_upload_status` char(1) DEFAULT NULL,
  `customer_product_name` varchar(30) NOT NULL,
  `order_id` bigint NOT NULL,
  `shoe_id` bigint NOT NULL,
  `business_technical_remark` varchar(50) DEFAULT NULL,
  `business_material_remark` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`order_shoe_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe`
--

LOCK TABLES `order_shoe` WRITE;
/*!40000 ALTER TABLE `order_shoe` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_shoe` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_shoe_batch_info`
--

DROP TABLE IF EXISTS `order_shoe_batch_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_shoe_batch_info` (
  `order_shoe_batch_info_id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL,
  `total_amount` int DEFAULT '0',
  `size_34_amount` int DEFAULT NULL,
  `size_35_amount` int DEFAULT NULL,
  `size_36_amount` int DEFAULT NULL,
  `size_37_amount` int DEFAULT NULL,
  `size_38_amount` int DEFAULT NULL,
  `size_39_amount` int DEFAULT NULL,
  `size_40_amount` int DEFAULT NULL,
  `size_41_amount` int DEFAULT NULL,
  `size_42_amount` int DEFAULT NULL,
  `size_43_amount` int DEFAULT NULL,
  `size_44_amount` int DEFAULT NULL,
  `size_45_amount` int DEFAULT NULL,
  `size_46_amount` int DEFAULT '0',
  `order_shoe_type_id` bigint NOT NULL,
  `price_per_pair` decimal(10,2) DEFAULT NULL,
  `total_price` decimal(10,2) DEFAULT NULL,
  `currency_type` char(3) DEFAULT NULL,
  `packaging_info_id` int DEFAULT NULL,
  `packaging_info_quantity` int DEFAULT NULL,
  PRIMARY KEY (`order_shoe_batch_info_id`),
  KEY `fk_order_shoe_shoesizes` (`order_shoe_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_batch_info`
--

LOCK TABLES `order_shoe_batch_info` WRITE;
/*!40000 ALTER TABLE `order_shoe_batch_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_shoe_batch_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_shoe_production_amount`
--

DROP TABLE IF EXISTS `order_shoe_production_amount`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_shoe_production_amount` (
  `order_shoe_production_amount_id` bigint NOT NULL AUTO_INCREMENT,
  `order_shoe_type_id` bigint NOT NULL,
  `size_34_production_amount` int DEFAULT '0',
  `size_35_production_amount` int DEFAULT '0',
  `size_36_production_amount` int DEFAULT '0',
  `size_37_production_amount` int DEFAULT '0',
  `size_38_production_amount` int DEFAULT '0',
  `size_39_production_amount` int DEFAULT '0',
  `size_40_production_amount` int DEFAULT '0',
  `size_41_production_amount` int DEFAULT '0',
  `size_42_production_amount` int DEFAULT '0',
  `size_43_production_amount` int DEFAULT '0',
  `size_44_production_amount` int DEFAULT '0',
  `size_45_production_amount` int DEFAULT '0',
  `size_46_production_amount` int DEFAULT '0',
  `total_production_amount` int DEFAULT NULL,
  `production_team` tinyint DEFAULT NULL COMMENT '0：裁断\n1：针车\n2：成型',
  PRIMARY KEY (`order_shoe_production_amount_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_production_amount`
--

LOCK TABLES `order_shoe_production_amount` WRITE;
/*!40000 ALTER TABLE `order_shoe_production_amount` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_shoe_production_amount` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_shoe_production_info`
--

DROP TABLE IF EXISTS `order_shoe_production_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_shoe_production_info` (
  `production_info_id` bigint NOT NULL AUTO_INCREMENT,
  `cutting_line_group` varchar(30) DEFAULT NULL,
  `pre_sewing_line_group` varchar(30) DEFAULT NULL,
  `sewing_line_group` varchar(30) DEFAULT NULL,
  `molding_line_group` varchar(30) DEFAULT NULL,
  `is_cutting_outsourced` tinyint(1) DEFAULT '0',
  `is_sewing_outsourced` tinyint(1) DEFAULT '0',
  `is_molding_outsourced` tinyint(1) DEFAULT '0',
  `cutting_start_date` date DEFAULT NULL,
  `cutting_end_date` date DEFAULT NULL,
  `pre_sewing_start_date` date DEFAULT NULL,
  `pre_sewing_end_date` date DEFAULT NULL,
  `sewing_start_date` date DEFAULT NULL,
  `sewing_end_date` date DEFAULT NULL,
  `molding_start_date` date DEFAULT NULL,
  `molding_end_date` date DEFAULT NULL,
  `is_material_arrived` tinyint(1) NOT NULL,
  `order_shoe_id` bigint NOT NULL,
  PRIMARY KEY (`production_info_id`),
  KEY `fk_order_shoe_production_info` (`order_shoe_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_production_info`
--

LOCK TABLES `order_shoe_production_info` WRITE;
/*!40000 ALTER TABLE `order_shoe_production_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_shoe_production_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_shoe_status`
--

DROP TABLE IF EXISTS `order_shoe_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_shoe_status` (
  `order_shoe_status_id` bigint NOT NULL AUTO_INCREMENT,
  `order_shoe_id` bigint NOT NULL,
  `current_status` int NOT NULL,
  `current_status_value` int NOT NULL,
  PRIMARY KEY (`order_shoe_status_id`),
  KEY `fk_order_shoe_status` (`order_shoe_id`),
  KEY `fk_order_shoe_status0` (`current_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_status`
--

LOCK TABLES `order_shoe_status` WRITE;
/*!40000 ALTER TABLE `order_shoe_status` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_shoe_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_shoe_status_reference`
--

DROP TABLE IF EXISTS `order_shoe_status_reference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_shoe_status_reference` (
  `status_id` int NOT NULL,
  `status_name` varchar(40) NOT NULL,
  PRIMARY KEY (`status_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_status_reference`
--

LOCK TABLES `order_shoe_status_reference` WRITE;
/*!40000 ALTER TABLE `order_shoe_status_reference` DISABLE KEYS */;
INSERT INTO `order_shoe_status_reference` VALUES (0,'投产指令单创建'),(1,'投产指令单下发'),(2,'一次BOM填写'),(3,'一次BOM下发'),(4,'面料单位用量计算'),(5,'面料单位用量下发'),(6,'一次采购订单创建'),(7,'一次采购订单下发'),(8,'一次采购入库'),(9,'技术部调版分配'),(10,'技术部调版下发'),(11,'二次BOM填写'),(12,'二次BOM下发'),(13,'二次采购订单创建'),(14,'二次采购订单下发'),(15,'二次采购入库'),(16,'材料到齐通知'),(17,'生产排期，分配'),(18,'生产开始'),(19,'裁断材料出库'),(20,'裁断，批皮工价填报'),(21,'财务部审核'),(22,'生产副总审核'),(23,'裁断开始'),(24,'裁断结束'),(25,'半成品中转入库'),(26,'半成品中转针车材料出库'),(27,'针车及预备工序填报'),(28,'财务部审核'),(29,'生产副总审核'),(30,'针车预备开始'),(31,'针车预备结束'),(32,'针车开始'),(33,'针车结束'),(34,'鞋包中转仓入库'),(35,'鞋包中转仓出库'),(36,'成型材料出库'),(37,'成型工价填报'),(38,'财务部审核'),(39,'生产副总审核'),(40,'成型开始'),(41,'成型结束'),(42,'生产结束');
/*!40000 ALTER TABLE `order_shoe_status_reference` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_shoe_type`
--

DROP TABLE IF EXISTS `order_shoe_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_shoe_type` (
  `order_shoe_type_id` bigint NOT NULL AUTO_INCREMENT,
  `shoe_type_id` bigint NOT NULL,
  `order_shoe_id` bigint NOT NULL,
  `cutting_amount` int DEFAULT (_utf8mb4'0'),
  `pre_sewing_amount` int DEFAULT (_utf8mb4'0'),
  `sewing_amount` int DEFAULT (_utf8mb4'0'),
  `molding_amount` int DEFAULT (_utf8mb4'0'),
  `workflow_id` varchar(45) DEFAULT NULL,
  `unit_price` decimal(10,2) DEFAULT '0.00',
  `currency_type` char(4) DEFAULT '',
  `total_amount` int DEFAULT '0',
  PRIMARY KEY (`order_shoe_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_type`
--

LOCK TABLES `order_shoe_type` WRITE;
/*!40000 ALTER TABLE `order_shoe_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_shoe_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_status`
--

DROP TABLE IF EXISTS `order_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_status` (
  `order_status_id` bigint NOT NULL AUTO_INCREMENT,
  `order_current_status` int NOT NULL,
  `order_status_value` int NOT NULL,
  `order_id` bigint NOT NULL,
  PRIMARY KEY (`order_status_id`),
  KEY `fk_order_status_order_status` (`order_id`),
  KEY `fk_order_status` (`order_current_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_status`
--

LOCK TABLES `order_status` WRITE;
/*!40000 ALTER TABLE `order_status` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_status_reference`
--

DROP TABLE IF EXISTS `order_status_reference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_status_reference` (
  `order_status_id` int NOT NULL,
  `order_status_name` varchar(40) NOT NULL,
  PRIMARY KEY (`order_status_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_status_reference`
--

LOCK TABLES `order_status_reference` WRITE;
/*!40000 ALTER TABLE `order_status_reference` DISABLE KEYS */;
INSERT INTO `order_status_reference` VALUES (0,'订单创建'),(1,'打样单创建'),(2,'打样单初步确认'),(3,'打样单分配'),(4,'打样单修改'),(5,'打样单最终确认'),(6,'生产订单创建'),(7,'生产订单总经理确认'),(8,'生产副总确认'),(9,'生产流程'),(10,'生产结束确认'),(11,'业务部确认'),(12,'业务部创建发货通知'),(13,'发货通知下发'),(14,'总经理确认'),(15,'成品仓发货'),(16,'发货量上传'),(17,'全部发货确认'),(18,'订单完成');
/*!40000 ALTER TABLE `order_status_reference` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `outbound_record`
--

DROP TABLE IF EXISTS `outbound_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outbound_record` (
  `outbound_record_id` bigint NOT NULL AUTO_INCREMENT,
  `outbound_rid` varchar(60) DEFAULT NULL,
  `outbound_amount` decimal(10,5) DEFAULT NULL,
  `size_34_outbound_amount` int DEFAULT NULL,
  `size_35_outbound_amount` int DEFAULT NULL,
  `size_36_outbound_amount` int DEFAULT NULL,
  `size_37_outbound_amount` int DEFAULT NULL,
  `size_38_outbound_amount` int DEFAULT NULL,
  `size_39_outbound_amount` int DEFAULT NULL,
  `size_40_outbound_amount` int DEFAULT NULL,
  `size_41_outbound_amount` int DEFAULT NULL,
  `size_42_outbound_amount` int DEFAULT NULL,
  `size_43_outbound_amount` int DEFAULT NULL,
  `size_44_outbound_amount` int DEFAULT NULL,
  `size_45_outbound_amount` int DEFAULT NULL,
  `size_46_outbound_amount` int DEFAULT NULL,
  `outbound_datetime` datetime NOT NULL,
  `outbound_type` tinyint NOT NULL DEFAULT (_utf8mb4'0') COMMENT '0：自产\n1：废料\n2：外包',
  `outbound_department` tinyint DEFAULT NULL COMMENT '0: cutting, 1: sewing, 2: molding',
  `picker` varchar(15) DEFAULT NULL,
  `outbound_address` varchar(100) DEFAULT NULL,
  `material_storage_id` bigint DEFAULT NULL,
  `size_material_storage_id` bigint DEFAULT NULL,
  `outsource_info_id` int DEFAULT NULL,
  PRIMARY KEY (`outbound_record_id`),
  KEY `fk_outstock_record` (`material_storage_id`),
  KEY `fk_outstock_record0` (`size_material_storage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `outbound_record`
--

LOCK TABLES `outbound_record` WRITE;
/*!40000 ALTER TABLE `outbound_record` DISABLE KEYS */;
/*!40000 ALTER TABLE `outbound_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `outsource_batch_info`
--

DROP TABLE IF EXISTS `outsource_batch_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outsource_batch_info` (
  `outsource_batch_info_id` bigint NOT NULL AUTO_INCREMENT,
  `order_shoe_type_id` bigint NOT NULL,
  `total_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_34_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_35_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_36_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_37_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_38_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_39_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_40_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_41_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_42_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_43_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_44_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_45_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `size_46_outsource_amount` int DEFAULT (_utf8mb4'0'),
  `outsource_info_id` int NOT NULL,
  `is_product_arrived` tinyint NOT NULL DEFAULT (_utf8mb4'0'),
  PRIMARY KEY (`outsource_batch_info_id`),
  KEY `fk_order_shoe_shoesizes_0` (`order_shoe_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `outsource_batch_info`
--

LOCK TABLES `outsource_batch_info` WRITE;
/*!40000 ALTER TABLE `outsource_batch_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `outsource_batch_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `outsource_cost_detail`
--

DROP TABLE IF EXISTS `outsource_cost_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outsource_cost_detail` (
  `outsource_cost_detail_id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(50) DEFAULT NULL,
  `item_cost` decimal(10,2) DEFAULT NULL,
  `outsource_info_id` int NOT NULL,
  `remark` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`outsource_cost_detail_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `outsource_cost_detail`
--

LOCK TABLES `outsource_cost_detail` WRITE;
/*!40000 ALTER TABLE `outsource_cost_detail` DISABLE KEYS */;
/*!40000 ALTER TABLE `outsource_cost_detail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `outsource_factory`
--

DROP TABLE IF EXISTS `outsource_factory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outsource_factory` (
  `factory_id` int NOT NULL,
  `factory_name` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`factory_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `outsource_factory`
--

LOCK TABLES `outsource_factory` WRITE;
/*!40000 ALTER TABLE `outsource_factory` DISABLE KEYS */;
/*!40000 ALTER TABLE `outsource_factory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `outsource_info`
--

DROP TABLE IF EXISTS `outsource_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outsource_info` (
  `outsource_info_id` int NOT NULL,
  `outsource_type` varchar(20) NOT NULL COMMENT '0=裁断\n1=针车\n2=成型',
  `factory_id` int NOT NULL,
  `outsource_amount` int NOT NULL DEFAULT '0',
  `outsource_start_date` date NOT NULL,
  `outsource_end_date` date NOT NULL,
  `outsource_status` tinyint NOT NULL COMMENT '0：未提交\n1：已提交\n2：已审批\n3：被驳回\n4：材料出库\n5：生产中\n6：成品入库\n7： 外包结束',
  `deadline_date` date NOT NULL,
  `material_required` tinyint(1) NOT NULL,
  `semifinished_required` tinyint(1) NOT NULL,
  `semifinished_estimated_outbound_date` date DEFAULT NULL,
  `material_estimated_outbound_date` date DEFAULT NULL,
  `order_shoe_id` bigint NOT NULL,
  `rejection_reason` varchar(50) DEFAULT NULL,
  `total_cost` decimal(10,2) DEFAULT (_utf8mb4'0'),
  `outbound_counter` tinyint DEFAULT (_utf8mb4'0'),
  PRIMARY KEY (`outsource_info_id`),
  KEY `fk_outsource_info_order_shoe` (`order_shoe_id`),
  KEY `fk_outsource_info_outsource_factory` (`factory_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `outsource_info`
--

LOCK TABLES `outsource_info` WRITE;
/*!40000 ALTER TABLE `outsource_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `outsource_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `packaging_info`
--

DROP TABLE IF EXISTS `packaging_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `packaging_info` (
  `packaging_info_id` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `packaging_info_name` varchar(10) NOT NULL,
  `packaging_info_locale` varchar(10) NOT NULL,
  `batch_info_type_id` int NOT NULL,
  `size_34_ratio` int DEFAULT '0',
  `size_35_ratio` int DEFAULT '0',
  `size_36_ratio` int DEFAULT '0',
  `size_37_ratio` int DEFAULT '0',
  `size_38_ratio` int DEFAULT '0',
  `size_39_ratio` int DEFAULT '0',
  `size_40_ratio` int DEFAULT '0',
  `size_41_ratio` int DEFAULT '0',
  `size_42_ratio` int DEFAULT '0',
  `size_43_ratio` int DEFAULT '0',
  `size_44_ratio` int DEFAULT '0',
  `size_45_ratio` int DEFAULT '0',
  `size_46_ratio` int DEFAULT '0',
  `total_quantity_ratio` int DEFAULT NULL,
  PRIMARY KEY (`packaging_info_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `packaging_info`
--

LOCK TABLES `packaging_info` WRITE;
/*!40000 ALTER TABLE `packaging_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `packaging_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `procedure_reference`
--

DROP TABLE IF EXISTS `procedure_reference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `procedure_reference` (
  `procedure_id` bigint NOT NULL AUTO_INCREMENT,
  `procedure_name` varchar(100) DEFAULT NULL,
  `team` varchar(10) DEFAULT NULL,
  `current_price` float DEFAULT NULL,
  PRIMARY KEY (`procedure_id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='裁断，针车，成型工序名字一览';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `procedure_reference`
--

LOCK TABLES `procedure_reference` WRITE;
/*!40000 ALTER TABLE `procedure_reference` DISABLE KEYS */;
INSERT INTO `procedure_reference` VALUES (2,'裁断1','裁断',1.1),(3,'裁断2','裁断',2.2),(4,'后跟合缝','针车预备',0.1),(6,'预备2','针车预备',12),(7,'预备3','针车预备',5),(8,'单针车内外边排','针车',0.36),(9,'车鞋眼片滴塑标4个','针车',0.5),(10,'反车后排里布放保险丝','针车',0.5),(11,'成型1','成型',1),(12,'成型2','成型',2),(13,'成型3','成型',3),(14,'单针车鞋眼片','针车',0.6),(15,'批皮-片22','裁断',1.47);
/*!40000 ALTER TABLE `procedure_reference` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `production_instruction`
--

DROP TABLE IF EXISTS `production_instruction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `production_instruction` (
  `production_instruction_id` bigint NOT NULL AUTO_INCREMENT,
  `production_instruction_rid` varchar(30) NOT NULL,
  `order_shoe_id` bigint NOT NULL,
  `production_instruction_status` char(1) DEFAULT NULL,
  `origin_size` varchar(5) DEFAULT NULL,
  `size_range` varchar(15) DEFAULT NULL,
  `size_difference` varchar(10) DEFAULT NULL,
  `last_type` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`production_instruction_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `production_instruction`
--

LOCK TABLES `production_instruction` WRITE;
/*!40000 ALTER TABLE `production_instruction` DISABLE KEYS */;
/*!40000 ALTER TABLE `production_instruction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `production_instruction_item`
--

DROP TABLE IF EXISTS `production_instruction_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `production_instruction_item` (
  `production_instruction_item_id` bigint NOT NULL AUTO_INCREMENT,
  `material_id` bigint NOT NULL,
  `production_instruction_id` bigint NOT NULL,
  `remark` varchar(40) DEFAULT NULL,
  `department_id` int DEFAULT NULL,
  `material_specification` varchar(60) DEFAULT NULL,
  `material_model` varchar(40) DEFAULT NULL,
  `color` varchar(10) DEFAULT NULL,
  `is_pre_purchase` tinyint(1) DEFAULT NULL,
  `material_type` char(1) DEFAULT NULL,
  `order_shoe_type_id` bigint NOT NULL,
  `material_second_type` varchar(10) DEFAULT NULL,
  `pic_note_status` tinyint DEFAULT (0),
  PRIMARY KEY (`production_instruction_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `production_instruction_item`
--

LOCK TABLES `production_instruction_item` WRITE;
/*!40000 ALTER TABLE `production_instruction_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `production_instruction_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_divide_order`
--

DROP TABLE IF EXISTS `purchase_divide_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_divide_order` (
  `purchase_divide_order_id` bigint NOT NULL AUTO_INCREMENT,
  `purchase_order_id` bigint NOT NULL,
  `purchase_divide_order_rid` varchar(50) NOT NULL,
  `purchase_order_remark` varchar(150) DEFAULT NULL,
  `purchase_order_environmental_request` varchar(150) DEFAULT NULL,
  `shipment_address` varchar(100) DEFAULT NULL,
  `shipment_deadline` varchar(100) DEFAULT NULL,
  `purchase_divide_order_type` char(1) NOT NULL DEFAULT (_utf8mb4'N'),
  PRIMARY KEY (`purchase_divide_order_id`),
  UNIQUE KEY `purchase_divide_order_rid_UNIQUE` (`purchase_divide_order_rid`),
  KEY `fk_purchase_divide_order` (`purchase_order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_divide_order`
--

LOCK TABLES `purchase_divide_order` WRITE;
/*!40000 ALTER TABLE `purchase_divide_order` DISABLE KEYS */;
/*!40000 ALTER TABLE `purchase_divide_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_order`
--

DROP TABLE IF EXISTS `purchase_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_order` (
  `purchase_order_id` bigint NOT NULL AUTO_INCREMENT,
  `bom_id` bigint DEFAULT NULL,
  `purchase_order_rid` varchar(50) NOT NULL,
  `purchase_order_type` char(1) DEFAULT NULL,
  `purchase_order_issue_date` date NOT NULL DEFAULT (curdate()),
  `order_id` bigint DEFAULT NULL,
  `purchase_order_status` char(1) DEFAULT NULL,
  PRIMARY KEY (`purchase_order_id`),
  UNIQUE KEY `purchase_order_rid_UNIQUE` (`purchase_order_rid`),
  KEY `fk_purchase_orders_boms` (`bom_id`),
  KEY `fk_purchase_order_order` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_order`
--

LOCK TABLES `purchase_order` WRITE;
/*!40000 ALTER TABLE `purchase_order` DISABLE KEYS */;
/*!40000 ALTER TABLE `purchase_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_order_item`
--

DROP TABLE IF EXISTS `purchase_order_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_order_item` (
  `purchase_order_item_id` bigint NOT NULL AUTO_INCREMENT,
  `bom_item_id` bigint NOT NULL,
  `purchase_divide_order_id` bigint NOT NULL,
  `purchase_amount` decimal(10,5) NOT NULL,
  `size_34_purchase_amount` int DEFAULT NULL,
  `size_35_purchase_amount` int DEFAULT NULL,
  `size_36_purchase_amount` int DEFAULT NULL,
  `size_37_purchase_amount` int DEFAULT NULL,
  `size_38_purchase_amount` int DEFAULT NULL,
  `size_39_purchase_amount` int DEFAULT NULL,
  `size_40_purchase_amount` int DEFAULT NULL,
  `size_41_purchase_amount` int DEFAULT NULL,
  `size_42_purchase_amount` int DEFAULT NULL,
  `size_43_purchase_amount` int DEFAULT NULL,
  `size_44_purchase_amount` int DEFAULT NULL,
  `size_45_purchase_amount` int DEFAULT NULL,
  `size_46_purchase_amount` int DEFAULT NULL,
  PRIMARY KEY (`purchase_order_item_id`),
  KEY `fk_purchase_order_items_bom_item` (`bom_item_id`),
  KEY `fk_purchase_order_items` (`purchase_divide_order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_order_item`
--

LOCK TABLES `purchase_order_item` WRITE;
/*!40000 ALTER TABLE `purchase_order_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `purchase_order_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quantity_report`
--

DROP TABLE IF EXISTS `quantity_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quantity_report` (
  `report_id` bigint NOT NULL AUTO_INCREMENT,
  `order_shoe_id` bigint NOT NULL,
  `team` enum('裁断','针车预备','针车','成型') NOT NULL,
  `creation_date` date DEFAULT NULL,
  `submission_date` date DEFAULT NULL,
  `status` tinyint NOT NULL,
  `rejection_reason` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`report_id`),
  KEY `fk_cutting_quantity_report_order_shoe` (`order_shoe_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quantity_report`
--

LOCK TABLES `quantity_report` WRITE;
/*!40000 ALTER TABLE `quantity_report` DISABLE KEYS */;
/*!40000 ALTER TABLE `quantity_report` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quantity_report_item`
--

DROP TABLE IF EXISTS `quantity_report_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quantity_report_item` (
  `quantity_report_item_id` bigint NOT NULL AUTO_INCREMENT,
  `quantity_report_id` bigint NOT NULL,
  `order_shoe_type_id` bigint NOT NULL,
  `report_amount` int DEFAULT '0',
  PRIMARY KEY (`quantity_report_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quantity_report_item`
--

LOCK TABLES `quantity_report_item` WRITE;
/*!40000 ALTER TABLE `quantity_report_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `quantity_report_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `report_template_detail`
--

DROP TABLE IF EXISTS `report_template_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_template_detail` (
  `report_template_id` int NOT NULL,
  `row_id` int NOT NULL,
  `procedure_name` varchar(50) DEFAULT NULL,
  `price` float DEFAULT NULL,
  `note` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`report_template_id`,`row_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `report_template_detail`
--

LOCK TABLES `report_template_detail` WRITE;
/*!40000 ALTER TABLE `report_template_detail` DISABLE KEYS */;
/*!40000 ALTER TABLE `report_template_detail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `semifinished_shoe_storage`
--

DROP TABLE IF EXISTS `semifinished_shoe_storage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `semifinished_shoe_storage` (
  `semifinished_shoe_id` bigint NOT NULL AUTO_INCREMENT,
  `semifinished_inbound_datetime` datetime DEFAULT NULL,
  `order_shoe_type_id` bigint NOT NULL,
  `semifinished_amount` int NOT NULL DEFAULT '0',
  `semifinished_status` tinyint DEFAULT NULL COMMENT '0：未入库\n1：已入库\n2：已出库',
  `semifinished_object` tinyint DEFAULT NULL COMMENT '0: 半成品\n1: 鞋包',
  PRIMARY KEY (`semifinished_shoe_id`),
  KEY `fk_semifinished_shoe_storage` (`order_shoe_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `semifinished_shoe_storage`
--

LOCK TABLES `semifinished_shoe_storage` WRITE;
/*!40000 ALTER TABLE `semifinished_shoe_storage` DISABLE KEYS */;
/*!40000 ALTER TABLE `semifinished_shoe_storage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shoe`
--

DROP TABLE IF EXISTS `shoe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shoe` (
  `shoe_id` int NOT NULL AUTO_INCREMENT,
  `shoe_rid` varchar(30) NOT NULL,
  `shoe_designer` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`shoe_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shoe`
--

LOCK TABLES `shoe` WRITE;
/*!40000 ALTER TABLE `shoe` DISABLE KEYS */;
/*!40000 ALTER TABLE `shoe` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shoe_inbound_record`
--

DROP TABLE IF EXISTS `shoe_inbound_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shoe_inbound_record` (
  `shoe_inbound_record_id` bigint NOT NULL AUTO_INCREMENT,
  `shoe_inbound_rid` varchar(60) DEFAULT NULL,
  `inbound_amount` int DEFAULT NULL,
  `inbound_revenue` decimal(10,2) DEFAULT NULL,
  `subsequent_stock` int DEFAULT NULL,
  `subsequent_revenue` decimal(10,2) DEFAULT NULL,
  `inbound_datetime` datetime NOT NULL,
  `inbound_type` tinyint NOT NULL DEFAULT (_utf8mb4'0') COMMENT '0: 自产\n1: 外包',
  `semifinished_shoe_storage_id` bigint DEFAULT NULL,
  `finished_shoe_storage_id` bigint DEFAULT NULL,
  `outsource_info_id` int DEFAULT NULL,
  PRIMARY KEY (`shoe_inbound_record_id`),
  KEY `fk_shoe_instock_record` (`semifinished_shoe_storage_id`),
  KEY `fk_shoe_instock_record0` (`finished_shoe_storage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shoe_inbound_record`
--

LOCK TABLES `shoe_inbound_record` WRITE;
/*!40000 ALTER TABLE `shoe_inbound_record` DISABLE KEYS */;
/*!40000 ALTER TABLE `shoe_inbound_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shoe_outbound_record`
--

DROP TABLE IF EXISTS `shoe_outbound_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shoe_outbound_record` (
  `shoe_outbound_record_id` bigint NOT NULL AUTO_INCREMENT,
  `shoe_outbound_rid` varchar(60) DEFAULT NULL,
  `outbound_amount` int DEFAULT NULL,
  `outbound_revenue` decimal(10,2) DEFAULT NULL,
  `subsequent_stock` int DEFAULT NULL,
  `subsequent_revenue` decimal(10,2) DEFAULT NULL,
  `outbound_datetime` datetime NOT NULL,
  `outbound_address` varchar(100) DEFAULT NULL,
  `outbound_type` tinyint NOT NULL DEFAULT '0',
  `outbound_department` tinyint DEFAULT '0',
  `picker` varchar(15) DEFAULT NULL,
  `semifinished_shoe_storage_id` bigint DEFAULT NULL,
  `finished_shoe_storage_id` bigint DEFAULT NULL,
  `outsource_info_id` int DEFAULT NULL,
  PRIMARY KEY (`shoe_outbound_record_id`),
  KEY `fk_shoe_outstock_record` (`semifinished_shoe_storage_id`),
  KEY `fk_shoe_outstock_record0` (`finished_shoe_storage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shoe_outbound_record`
--

LOCK TABLES `shoe_outbound_record` WRITE;
/*!40000 ALTER TABLE `shoe_outbound_record` DISABLE KEYS */;
/*!40000 ALTER TABLE `shoe_outbound_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shoe_part`
--

DROP TABLE IF EXISTS `shoe_part`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shoe_part` (
  `shoe_part_id` int NOT NULL AUTO_INCREMENT,
  `shoe_part_name` varchar(30) NOT NULL,
  PRIMARY KEY (`shoe_part_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shoe_part`
--

LOCK TABLES `shoe_part` WRITE;
/*!40000 ALTER TABLE `shoe_part` DISABLE KEYS */;
/*!40000 ALTER TABLE `shoe_part` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shoe_type`
--

DROP TABLE IF EXISTS `shoe_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shoe_type` (
  `shoe_type_id` bigint NOT NULL AUTO_INCREMENT,
  `shoe_image_url` varchar(100) DEFAULT NULL,
  `color_id` int NOT NULL,
  `shoe_id` int NOT NULL,
  PRIMARY KEY (`shoe_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shoe_type`
--

LOCK TABLES `shoe_type` WRITE;
/*!40000 ALTER TABLE `shoe_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `shoe_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `size_material_storage`
--

DROP TABLE IF EXISTS `size_material_storage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `size_material_storage` (
  `size_material_storage_id` bigint NOT NULL AUTO_INCREMENT,
  `size_material_specification` varchar(40) NOT NULL,
  `size_34_estimated_inbound_amount` int DEFAULT '0',
  `size_35_estimated_inbound_amount` int DEFAULT '0',
  `size_36_estimated_inbound_amount` int DEFAULT '0',
  `size_37_estimated_inbound_amount` int DEFAULT '0',
  `size_38_estimated_inbound_amount` int DEFAULT '0',
  `size_39_estimated_inbound_amount` int DEFAULT '0',
  `size_40_estimated_inbound_amount` int DEFAULT '0',
  `size_41_estimated_inbound_amount` int DEFAULT '0',
  `size_42_estimated_inbound_amount` int DEFAULT '0',
  `size_43_estimated_inbound_amount` int DEFAULT '0',
  `size_44_estimated_inbound_amount` int DEFAULT '0',
  `size_45_estimated_inbound_amount` int DEFAULT '0',
  `size_46_estimated_inbound_amount` int DEFAULT '0',
  `total_estimated_inbound_amount` int DEFAULT '0',
  `size_34_actual_inbound_amount` int DEFAULT '0',
  `size_35_actual_inbound_amount` int DEFAULT '0',
  `size_36_actual_inbound_amount` int DEFAULT '0',
  `size_37_actual_inbound_amount` int DEFAULT '0',
  `size_38_actual_inbound_amount` int DEFAULT '0',
  `size_39_actual_inbound_amount` int DEFAULT '0',
  `size_40_actual_inbound_amount` int DEFAULT '0',
  `size_41_actual_inbound_amount` int DEFAULT '0',
  `size_42_actual_inbound_amount` int DEFAULT '0',
  `size_43_actual_inbound_amount` int DEFAULT '0',
  `size_44_actual_inbound_amount` int DEFAULT '0',
  `size_45_actual_inbound_amount` int DEFAULT '0',
  `size_46_actual_inbound_amount` int DEFAULT '0',
  `total_actual_inbound_amount` int DEFAULT '0',
  `material_outsource_status` char(1) DEFAULT (_utf8mb4'N'),
  `size_34_current_amount` int NOT NULL DEFAULT (0),
  `size_35_current_amount` int NOT NULL DEFAULT (0),
  `size_36_current_amount` int NOT NULL DEFAULT (0),
  `size_37_current_amount` int NOT NULL DEFAULT (0),
  `size_38_current_amount` int NOT NULL DEFAULT (0),
  `size_39_current_amount` int NOT NULL DEFAULT (0),
  `size_40_current_amount` int NOT NULL DEFAULT (0),
  `size_41_current_amount` int NOT NULL DEFAULT (0),
  `size_42_current_amount` int NOT NULL DEFAULT (0),
  `size_43_current_amount` int NOT NULL DEFAULT (0),
  `size_44_current_amount` int NOT NULL DEFAULT (0),
  `size_45_current_amount` int NOT NULL DEFAULT (0),
  `size_46_current_amount` int NOT NULL DEFAULT (0),
  `total_current_amount` int NOT NULL DEFAULT (0),
  `size_storage_type` char(1) NOT NULL DEFAULT (_utf8mb4'E'),
  `material_outsource_date` date DEFAULT NULL,
  `material_id` bigint NOT NULL,
  `size_material_color` varchar(40) DEFAULT NULL,
  `order_shoe_id` bigint DEFAULT NULL,
  `unit_price` decimal(10,2) DEFAULT NULL,
  `purchase_divide_order_id` bigint DEFAULT NULL,
  `material_estimated_arrival_date` date DEFAULT NULL,
  `size_material_model` varchar(40) DEFAULT NULL,
  `material_storage_status` tinyint DEFAULT NULL,
  PRIMARY KEY (`size_material_storage_id`),
  KEY `fk_size_material_storage0` (`material_id`),
  KEY `fk_size_material_storage_color` (`size_material_color`),
  KEY `fk_size_material_storage` (`order_shoe_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `size_material_storage`
--

LOCK TABLES `size_material_storage` WRITE;
/*!40000 ALTER TABLE `size_material_storage` DISABLE KEYS */;
/*!40000 ALTER TABLE `size_material_storage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff`
--

DROP TABLE IF EXISTS `staff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff` (
  `staff_id` int NOT NULL AUTO_INCREMENT,
  `staff_name` varchar(20) NOT NULL,
  `character_id` int NOT NULL,
  `department_id` int NOT NULL,
  PRIMARY KEY (`staff_id`),
  KEY `fk_staffs_staffs` (`character_id`),
  KEY `fk_staffs_departments` (`department_id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff`
--

LOCK TABLES `staff` WRITE;
/*!40000 ALTER TABLE `staff` DISABLE KEYS */;
INSERT INTO `staff` VALUES (1,'吴启龙',14,9),(2,'谢海涵',2,8),(3,'谢树洼',9,6),(4,'黄培培',10,13),(5,'邹远东',6,4),(6,'豆德成',16,4),(7,'周伟',7,11),(8,'孙汝满',7,11),(9,'舒克能',7,11),(10,'张伟芳',4,10),(11,'范建明',8,12),(13,'潘璟',5,5),(14,'姜',18,11),(15,'技术部文员',17,5),(16,'生产副总',3,4),(17,'裁断',11,4),(18,'针车',12,4),(19,'成型',13,4),(20,'半成品',19,12),(21,'成品',20,12),(22,'业务部文员1',21,10);
/*!40000 ALTER TABLE `staff` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `supplier`
--

DROP TABLE IF EXISTS `supplier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `supplier` (
  `supplier_id` int NOT NULL AUTO_INCREMENT,
  `supplier_name` varchar(50) NOT NULL,
  `supplier_type` char(1) DEFAULT (_utf8mb4'N'),
  PRIMARY KEY (`supplier_id`)
) ENGINE=InnoDB AUTO_INCREMENT=209 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier`
--

LOCK TABLES `supplier` WRITE;
/*!40000 ALTER TABLE `supplier` DISABLE KEYS */;
INSERT INTO `supplier` VALUES (1,'询价','N'),(2,'采购员','N'),(3,'行政采购','N'),(4,'商务采购','N'),(5,'豪富达中底','N'),(6,'森达鞋楦','N'),(7,'昊宇鞋楦','N'),(8,'佳明粉胶','N'),(9,'科盛化工','N'),(10,'小东化工','N'),(11,'瓯海纸业','N'),(12,'珍和鞋盒','N'),(13,'阿其鞋盒','N'),(14,'阿孟鞋盒','N'),(15,'东鑫包装','N'),(16,'炜一刀模','N'),(17,'鸿达刀模','N'),(18,'华一线业','N'),(19,'灯塔线业','N'),(20,'卓玛鞋材','N'),(21,'秀莲鞋材','N'),(22,'旭东鞋材','N'),(23,'兴元印刷','N'),(24,'创辉底材','N'),(25,'日禾底材','N'),(26,'双泰底材','N'),(27,'大富豪底材','N'),(28,'汇丰鞋跟','N'),(29,'嘉泰皮革','N'),(30,'瑞佳皮革','N'),(31,'宝社皮革','N'),(32,'伟翔底材','N'),(33,'川东底材','N'),(34,'正东底材','N'),(35,'东莞鑫峰达底材','N'),(36,'一一鞋材','N'),(37,'秀莲鞋眼','N'),(38,'佳明针车行','N'),(39,'刘可蒙副食品','N'),(40,'胜国鞋扣','N'),(41,'宏锦皮革','N'),(42,'吉隆利发印刷厂','N'),(43,'福秀鞋材','N'),(44,'双榜拉链','N'),(45,'尚景饰扣','N'),(46,'瑞祥五金','N'),(47,'茂利皮革','N'),(48,'卓尔丝印板','N'),(49,'大丰鞋材','N'),(50,'嘉锦底材','N'),(51,'天塑皮革','N'),(52,'联创鞋材','N'),(53,'沃德利鞋材','N'),(54,'海龙皮毛','N'),(55,'君远纺织','N'),(56,'麦斯克条码','N'),(57,'曼凌鞋扣','N'),(58,'晴鑫鞋材','N'),(59,'润丰皮革','N'),(60,'宏锦皮革-东莞','N'),(61,'万锦纺织','N'),(62,'唯佳皮革','N'),(63,'鸿源皮革','N'),(64,'迦力底材','N'),(65,'约西底材','N'),(66,'广联底材','N'),(67,'万宇鞋材','N'),(68,'崎云布标','N'),(69,'和合拉链','N'),(70,'国茂皮革','N'),(71,'齐轩包装','N'),(72,'强大鞋材','N'),(73,'金凤中底厂','N'),(74,'顺达五金','N'),(75,'丰玲飞织','N'),(76,'福建义可底材','N'),(77,'东莞稳多多底材','N'),(78,'爱迪尔皮革','N'),(79,'齐雅皮革','N'),(80,'强锋皮革','N'),(81,'深源皮革','N'),(82,'海信皮标','N'),(83,'添鸿皮革','N'),(84,'登革路皮革','N'),(85,'南力化工','N'),(86,'瓯瑞皮革','N'),(87,'黄隆鞋机','N'),(88,'欧聚鞋材','N'),(89,'昊宇底材','N'),(90,'建斌鞋材','N'),(91,'华盛鞋盒','N'),(92,'东莞鸿泰鞋材','N'),(93,'申明鞋机','N'),(94,'永旭皮革','N'),(95,'惠东博泰皮革','N'),(96,'东日底材','N'),(97,'亿嘉皮革','N'),(98,'宏益皮业','N'),(99,'鑫福包装','N'),(100,'东莞骏华拉链','N'),(101,'远足鞋楦','N'),(102,'小安鞋底','N'),(103,'东莞林发鞋楦','N'),(104,'东莞冠鑫鞋材','N'),(105,'东莞悦盛鞋材','N'),(106,'惠东六合皮革','N'),(107,'深澳中底','N'),(108,'宏森皮革','N'),(109,'胜亮鞋材','N'),(110,'鞋艺笔业','N'),(111,'富昌织带','N'),(112,'沣进特材','N'),(113,'嘉隆底材','N'),(114,'方圆底材','N'),(115,'福建辉煌皮革','N'),(116,'创立底材','N'),(117,'博鑫鞋材','N'),(118,'三秦鞋跟','N'),(119,'保利特材','N'),(120,'东莞隆泰皮革','N'),(121,'新浪鞋跟','N'),(122,'胜丰皮业','N'),(123,'阿里皮业','N'),(124,'浙礼底材','N'),(125,'同人底材','N'),(126,'双禾皮革','N'),(127,'赛能皮革','N'),(128,'远鸿鞋材','N'),(129,'国星皮革','N'),(130,'中瑞中底','N'),(131,'风象鞋材','N'),(132,'阿里巴巴皮业','N'),(133,'鑫博底材','N'),(134,'汇鑫鞋模','N'),(135,'大丰收底材','N'),(136,'丰收针织','N'),(137,'晋江佐源底材','N'),(138,'泉州曾村底材','N'),(139,'华邦皮革','N'),(140,'齐业鞋材','N'),(141,'布凡鞋材','N'),(142,'网中网鞋材','N'),(143,'双峰底材','N'),(144,'谐和鞋材','N'),(145,'鹤羽底材','N'),(146,'京源皮革','N'),(147,'宏盛鞋材','N'),(148,'飞宇布业','N'),(149,'海景鞋材','N'),(150,'美帝皮革','N'),(151,'发发特材','N'),(152,'志坚鞋盒','N'),(153,'尼西皮革','N'),(154,'晟灏制袋','N'),(155,'东莞轩凯皮革','N'),(156,'千嘉亿皮业','N'),(157,'斯塔尔化工','N'),(158,'东莞正祺纺织','N'),(159,'东莞琪峰底材','N'),(160,'超颖鞋材','N'),(161,'东莞广艺鞋楦','N'),(162,'星圣皮革','N'),(163,'邦宏鞋材','N'),(164,'振奋底材','N'),(165,'东莞信辉皮革','N'),(166,'高崎机械','N'),(167,'旭都包装','N'),(168,'源祺鞋材','N'),(169,'意元鞋材','N'),(170,'宏毅达鞋材','N'),(171,'豪锦皮革','N'),(172,'宝莱皮革','N'),(173,'宝来皮革','N'),(174,'上品皮革','N'),(175,'忠良皮革','N'),(176,'晋江牛丝顿底材','N'),(177,'亿威底材','N'),(178,'嘉杰鞋楦','N'),(179,'米沙利服材','N'),(180,'正鸿皮革','N'),(181,'勇丰刀模','N'),(182,'晋江晟仁底材','N'),(183,'东莞君硕鞋材','N'),(184,'广州硕艺涵伊鞋材','N'),(185,'茶山工艺印刷厂','N'),(186,'克豪底材','N'),(187,'东印智造包装','N'),(188,'三友皮业','N'),(189,'兴欣复合','W'),(190,'富潮复合','W'),(191,'金乡加工','W'),(192,'康鸿加工','W'),(193,'创本鞋材','W'),(194,'阿春印花加工','W'),(195,'理想印花加工','W'),(196,'朱立东加工','W'),(197,'方平绣花加工','W'),(198,'阿军丝印','W'),(199,'鑫泽加工','W'),(200,'尹敬加工','W'),(201,'马旦激光加工','W'),(202,'源达加工','W'),(203,'阿强加工','W'),(204,'花蕾','W'),(205,'悦泰鞋材','W'),(206,'吴志丁加工','W'),(207,'鸿运鞋材','N'),(208,'深博','N');
/*!40000 ALTER TABLE `supplier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `total_bom`
--

DROP TABLE IF EXISTS `total_bom`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `total_bom` (
  `total_bom_id` bigint NOT NULL AUTO_INCREMENT,
  `total_bom_rid` varchar(40) NOT NULL,
  `order_shoe_id` bigint DEFAULT NULL,
  PRIMARY KEY (`total_bom_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `total_bom`
--

LOCK TABLES `total_bom` WRITE;
/*!40000 ALTER TABLE `total_bom` DISABLE KEYS */;
/*!40000 ALTER TABLE `total_bom` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `unit_price_report`
--

DROP TABLE IF EXISTS `unit_price_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unit_price_report` (
  `report_id` bigint NOT NULL AUTO_INCREMENT,
  `order_shoe_id` bigint NOT NULL,
  `submission_date` date DEFAULT NULL,
  `team` enum('裁断','针车预备','针车','成型') DEFAULT NULL,
  `status` tinyint NOT NULL,
  `rejection_reason` varchar(40) DEFAULT NULL,
  `price_sum` decimal(10,2) DEFAULT (_utf8mb4'0'),
  PRIMARY KEY (`report_id`),
  KEY `fk_unit_price_report_order_shoe` (`order_shoe_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='status: \n0 saved, \n1 submitted, \n2 approved';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `unit_price_report`
--

LOCK TABLES `unit_price_report` WRITE;
/*!40000 ALTER TABLE `unit_price_report` DISABLE KEYS */;
/*!40000 ALTER TABLE `unit_price_report` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `unit_price_report_detail`
--

DROP TABLE IF EXISTS `unit_price_report_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unit_price_report_detail` (
  `report_id` bigint NOT NULL,
  `row_id` int NOT NULL,
  `procedure_name` varchar(50) NOT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `note` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`report_id`,`row_id`),
  KEY `fk_unit_price_report_detail_procedure_reference` (`procedure_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `unit_price_report_detail`
--

LOCK TABLES `unit_price_report_detail` WRITE;
/*!40000 ALTER TABLE `unit_price_report_detail` DISABLE KEYS */;
/*!40000 ALTER TABLE `unit_price_report_detail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `unit_price_report_template`
--

DROP TABLE IF EXISTS `unit_price_report_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unit_price_report_template` (
  `template_id` int NOT NULL AUTO_INCREMENT,
  `shoe_id` int NOT NULL,
  `team` tinyint NOT NULL,
  PRIMARY KEY (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `unit_price_report_template`
--

LOCK TABLES `unit_price_report_template` WRITE;
/*!40000 ALTER TABLE `unit_price_report_template` DISABLE KEYS */;
/*!40000 ALTER TABLE `unit_price_report_template` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `user_name` varchar(100) NOT NULL,
  `user_passwd` varchar(80) NOT NULL,
  `staff_id` int DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  KEY `fk_user_staff` (`staff_id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'wuqilong','21232f297a57a5a743894a0e4a801fc3',1),(2,'xiehaihan','21232f297a57a5a743894a0e4a801fc3',2),(3,'xieshuwa','21232f297a57a5a743894a0e4a801fc3',3),(5,'zhouwei','21232f297a57a5a743894a0e4a801fc3',7),(6,'technicalclerk','21232f297a57a5a743894a0e4a801fc3',15),(7,'jianglaoshi','21232f297a57a5a743894a0e4a801fc3',14),(8,'zhangweifang','21232f297a57a5a743894a0e4a801fc3',10),(9,'fanjianming','21232f297a57a5a743894a0e4a801fc3',11),(10,'zouyuandong','21232f297a57a5a743894a0e4a801fc3',5),(11,'panjing','21232f297a57a5a743894a0e4a801fc3',13),(12,'fuzong','21232f297a57a5a743894a0e4a801fc3',16),(13,'caiduan','21232f297a57a5a743894a0e4a801fc3',17),(14,'zhenche','21232f297a57a5a743894a0e4a801fc3',18),(15,'chengxing','21232f297a57a5a743894a0e4a801fc3',19),(16,'banchengping','21232f297a57a5a743894a0e4a801fc3',20),(17,'chengping','21232f297a57a5a743894a0e4a801fc3',21),(18,'yewubu1','21232f297a57a5a743894a0e4a801fc3',22);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-11-22 21:41:36
