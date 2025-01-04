CREATE DATABASE  IF NOT EXISTS `jiancheng` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `jiancheng`;
-- MySQL dump 10.13  Distrib 8.0.36, for Linux (x86_64)
--
-- Host: 192.168.16.100    Database: jiancheng
-- ------------------------------------------------------
-- Server version	8.0.40-0ubuntu0.22.04.1

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
  `material_model` varchar(50) DEFAULT NULL,
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
  `size_type` char(10) NOT NULL DEFAULT 'E',
  `craft_name` varchar(200) DEFAULT NULL,
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
  `batch_info_type_usage` tinyint DEFAULT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `batch_info_type`
--

LOCK TABLES `batch_info_type` WRITE;
/*!40000 ALTER TABLE `batch_info_type` DISABLE KEYS */;
INSERT INTO `batch_info_type` VALUES (16,'US男',0,'7','7.5','8','8.5','9','9.5','10','10.5','11','11.5','12','12.5','13'),(17,'US女',0,'4','4.5','5','5.5','6','6.5','7','7.5','8','8.5','9','9.5','10'),(19,'童鞋',0,'28','29','30','31','32','33','34','35','36','37','38','39',''),(21,'EU男',0,'39','40','41','42','43','44','45','46','47','','','',''),(22,'EU女',0,'35','36','37','38','39','40','41','42','','','','','');
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
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `craft_name` varchar(200) DEFAULT NULL,
  `pairs` decimal(10,5) DEFAULT NULL,
  `production_instruction_item_id` bigint DEFAULT NULL,
  PRIMARY KEY (`bom_item_id`),
  KEY `fk_bom_items_departments` (`department_id`),
  KEY `fk_bom_items_materials` (`material_id`),
  KEY `fk_bom_items_boms` (`bom_id`),
  KEY `fk_bom_item_color` (`bom_item_color`)
) ENGINE=InnoDB AUTO_INCREMENT=190 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `character`
--

LOCK TABLES `character` WRITE;
/*!40000 ALTER TABLE `character` DISABLE KEYS */;
INSERT INTO `character` VALUES (1,'超级管理员'),(2,'董事长/总经理'),(3,'生产副总'),(4,'业务部经理'),(5,'技术部经理'),(6,'生产部经理'),(7,'开发经理'),(8,'总仓经理'),(9,'物控部经理'),(10,'财务部经理'),(11,'裁断主任'),(12,'针车主任'),(13,'成型主任'),(14,'人事部经理'),(15,'行政部经理'),(16,'品质部经理'),(17,'技术文员'),(18,'用量计算'),(19,'半成品仓管理员'),(20,'成品仓管理员'),(21,'业务部文员');
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
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `color`
--

LOCK TABLES `color` WRITE;
/*!40000 ALTER TABLE `color` DISABLE KEYS */;
INSERT INTO `color` VALUES (1,'黑色','','',''),(2,'灰色','','',''),(3,'棕色','BROWN','MARRON',''),(4,'深蓝','NAVY','NAVY',''),(5,'黑色','BLACK','',''),(6,'米色','BEIGE','',''),(7,'牛仔蓝','JEANS','',''),(9,'褐色','TAUPE','',''),(10,'驼色','CAMEL','CAMEL',''),(11,'枪色','PLUMB/GUN/PEWTER','PLOMO',''),(12,'军绿','','',''),(13,'冰色','','',''),(14,'古铜','','',''),(15,'酒红色','','',''),(16,'卡其色','','',''),(17,'卡其色','','',''),(18,'卡其色','','',''),(19,'绿色','GREEN','','');
/*!40000 ALTER TABLE `color` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `craft_sheet`
--

DROP TABLE IF EXISTS `craft_sheet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `craft_sheet` (
  `craft_sheet_id` bigint NOT NULL AUTO_INCREMENT,
  `craft_sheet_rid` varchar(40) DEFAULT NULL,
  `order_shoe_id` bigint DEFAULT NULL,
  `cut_die_staff` varchar(20) DEFAULT NULL,
  `production_remark` varchar(50) DEFAULT NULL,
  `cutting_special_process` varchar(150) DEFAULT NULL,
  `sewing_special_process` varchar(150) DEFAULT NULL,
  `molding_special_process` varchar(200) DEFAULT NULL,
  `post_processing_comment` varchar(150) DEFAULT NULL,
  `oily_glue` varchar(300) DEFAULT NULL,
  `cut_die_img_path` varchar(100) DEFAULT NULL,
  `pic_note_img_path` varchar(100) DEFAULT NULL,
  `craft_sheet_status` char(1) NOT NULL,
  `reviewer` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`craft_sheet_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `craft_sheet`
--

LOCK TABLES `craft_sheet` WRITE;
/*!40000 ALTER TABLE `craft_sheet` DISABLE KEYS */;
INSERT INTO `craft_sheet` VALUES (1,'202412041617351601503CS',5,'鸿达','产前试做每码各5双','','车线针距：面料合缝1.5MM,PU里合缝1.5MM,布里合缝2-3MM,\n贴里布要服贴帮面，贴主根包头放到位.鞋口里要抓弧度贴。鞋口贴保险带丝\n头排定型热两刀，冷一刀。时间热3秒，冷7秒\n','所有后跟合缝的鞋款后帮定型机定过再夹包，所有后跟包脚13MM\n组合底：80℃ 组合底：80℃，TPR:90，PU:85℃，冬季温度高5℃，压合7秒，13公斤','①-驼喷棕色线条+头尾','TPR底：894K处理剂，PU底：892R处理剂，EVA底：895E处理剂-使用时加15%E-750,\n橡胶底：①黑色用893R处理剂加3%粉1000ML加30克，②白色底用893S处理剂加2%粉1000ML加20克，PU革面：892R处理剂，尼龙布.绒皮：798P无色尼龙处理剂使用加15%E-750','http://192.168.16.100:12667/K24-003测/3E1122/刀模图/daomo-3e1122.png','http://192.168.16.100:12667/K24-003测/3E1122/图样备注/商标-3e1122.png','3',''),(2,'202412092047217068119CS',8,'炜一','产前试做每码5双',' 后排布里内侧定位处转印标①②③白底灰字(业务提供)','车线针距：面料合缝1.5MM,PU里合缝1.5MM,布里合缝2-3MM,贴里布要服贴帮面，贴子根包头放到位.棉鞋上口里要抓弧度贴车拉链拉链布留空1.5MM，拉链不能有高低现象。鞋口放保险丝\n头排定型热两刀,冷一刀.时间热3秒,冷7秒\n部件2.3搭接好，车好拉链再贴PU里,然后外发激光(康鸿激光) ','所有后跟合缝的鞋款后帮定型机定过再夹包，所有后跟包脚13MM组合底：80℃，TPR:90℃，PU:85℃ 冬季温度高5℃。压合7秒13斤\n复底放针织棉','①米喷棕色线条②蓝喷黑色线条③褐喷棕色线条','TPR底：894K处理剂，PU底：892R处理剂，EVA底：895E处理剂-使用时加15%E-750,\n橡胶底：①黑色用893R处理剂加3%粉1000ML加30克，②白色底用893S处理剂加2%粉1000ML加20克，PU革面：892R处理剂，尼龙布.绒皮：798P无色尼龙处理剂使用加15%E-750','http://192.168.16.100:12667/K24-004测/JC3670-3A33/刀模图/微信截图_20241209210607.png','http://192.168.16.100:12667/K24-004测/JC3670-3A33/图样备注/图片2.png','3','');
/*!40000 ALTER TABLE `craft_sheet` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `craft_sheet_item`
--

DROP TABLE IF EXISTS `craft_sheet_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `craft_sheet_item` (
  `craft_sheet_item_id` bigint NOT NULL AUTO_INCREMENT,
  `craft_sheet_id` bigint DEFAULT NULL,
  `material_id` bigint DEFAULT NULL,
  `department_id` int DEFAULT NULL,
  `material_specification` varchar(60) DEFAULT NULL,
  `material_model` varchar(50) DEFAULT NULL,
  `color` varchar(10) DEFAULT NULL,
  `material_type` char(1) DEFAULT NULL,
  `material_second_type` varchar(10) DEFAULT NULL,
  `order_shoe_type_id` bigint DEFAULT NULL,
  `remark` varchar(40) DEFAULT NULL,
  `craft_name` varchar(200) DEFAULT NULL,
  `material_source` char(1) DEFAULT NULL,
  `pairs` decimal(10,5) DEFAULT NULL,
  `unit_usage` decimal(10,5) DEFAULT NULL,
  `total_usage` decimal(10,5) DEFAULT NULL,
  `after_usage_symbol` tinyint DEFAULT '0',
  `production_instruction_item_id` bigint DEFAULT NULL,
  PRIMARY KEY (`craft_sheet_item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=211 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `craft_sheet_item`
--

LOCK TABLES `craft_sheet_item` WRITE;
/*!40000 ALTER TABLE `craft_sheet_item` DISABLE KEYS */;
INSERT INTO `craft_sheet_item` VALUES (151,1,326,NULL,NULL,NULL,'黑','S',NULL,6,NULL,'复1.0棕切片+1.0膜+白定型布',NULL,15.00000,0.06667,0.00000,1,NULL),(152,1,326,NULL,NULL,NULL,'黑','S',NULL,6,NULL,'复1.2棕切片',NULL,9.00000,0.11111,0.00000,1,NULL),(153,1,326,NULL,NULL,NULL,'黑','S',NULL,6,NULL,'复100K驼无纺布',NULL,173.00000,0.00578,0.00000,1,NULL),(154,1,327,NULL,NULL,NULL,'黑灰','S',NULL,6,NULL,'复50K驼无纺布',NULL,40.00000,0.02500,0.00000,1,NULL),(155,1,316,NULL,NULL,'1501-1','黑','I',NULL,6,NULL,'折抽18/23mm宽',NULL,86.00000,0.01163,0.00000,1,NULL),(156,1,328,NULL,NULL,NULL,'黑','I',NULL,6,NULL,'复3mm黑海绵+离子布',NULL,6.30000,0.15873,0.00000,1,NULL),(157,1,329,NULL,'REFRESH',NULL,'古银','A',NULL,6,NULL,'',NULL,2.00000,0.50000,0.00000,1,NULL),(158,1,330,NULL,NULL,NULL,'黑','A',NULL,6,NULL,'',NULL,2.00000,0.50000,0.00000,1,NULL),(159,1,331,NULL,'REFRESH',NULL,'古银','A',NULL,6,NULL,'',NULL,2.00000,0.50000,0.00000,1,NULL),(160,1,332,NULL,NULL,NULL,'黑','A',NULL,6,NULL,'',NULL,2.00000,0.50000,0.00000,1,NULL),(161,1,333,NULL,NULL,'211050','红牛筋/米','O',NULL,6,NULL,'',NULL,0.00000,NULL,0.00000,1,NULL),(162,1,334,NULL,NULL,'E211050',NULL,'M',NULL,6,NULL,'',NULL,0.00000,NULL,0.00000,1,NULL),(163,1,335,NULL,NULL,'E211050','绿','L',NULL,6,NULL,'',NULL,0.00000,NULL,0.00000,1,NULL),(164,1,316,NULL,NULL,'1501-1','黑','I',NULL,6,NULL,'复5mm高丽棉(90密度蓝色)',NULL,34.00000,0.02941,0.00000,1,NULL),(165,2,326,NULL,NULL,'168','米色','S',NULL,8,NULL,'复1.0棕切片 +1.0膜+白定型布(2M/KG)(低温复合)(部件:1)',NULL,15.00000,0.06667,0.00000,1,NULL),(166,2,326,NULL,NULL,'168','米色','S',NULL,8,NULL,'复1.2棕切片 (低温复合)(部件:4)',NULL,28.30000,0.03534,0.00000,1,NULL),(167,2,326,NULL,NULL,'168','米色','S',NULL,8,NULL,'复白细布 +2*3白布(低温复合)(部件:2.3)',NULL,11.30000,0.08850,0.00000,1,NULL),(168,2,326,NULL,NULL,'168','米色','S',NULL,8,NULL,'复嘉泰1501-57米 (低温复合)(部件:5)(康鸿激光)',NULL,150.00000,0.00667,0.00000,1,NULL),(169,2,1,NULL,NULL,NULL,NULL,'S',NULL,8,NULL,NULL,NULL,0.00000,0.00000,0.00000,1,NULL),(170,2,316,NULL,NULL,'1501-57','米色','I',NULL,8,NULL,'上胶+PE纸',NULL,30.70000,0.03257,0.00000,1,NULL),(171,2,328,NULL,NULL,NULL,'红米','I',NULL,8,NULL,'复3mm白海绵+离子布',NULL,10.30000,0.09709,0.00000,1,NULL),(172,2,340,NULL,NULL,'1501-57','米色','A',NULL,8,'1.8*2.3折抽','对复(防爆)(刀冲)(需批搭地)',NULL,86.00000,0.01163,0.00000,1,NULL),(173,2,341,NULL,'Refresh',NULL,'古银色','A',NULL,8,NULL,NULL,NULL,0.50000,2.00000,0.00000,1,NULL),(174,2,342,NULL,'Refresh',NULL,'米色','A',NULL,8,'打码',NULL,NULL,0.50000,2.00000,0.00000,1,NULL),(175,2,343,NULL,'Refresh',NULL,'古银色','A',NULL,8,NULL,NULL,NULL,0.50000,2.00000,0.00000,1,NULL),(176,2,344,NULL,NULL,'2699','米色','A',NULL,8,NULL,NULL,NULL,0.00000,0.00000,0.00000,1,NULL),(177,2,345,NULL,NULL,'H076','米黄色','O',NULL,8,'大底激光Refresh商标',NULL,NULL,0.00000,NULL,0.00000,1,NULL),(178,2,347,NULL,NULL,'H076',NULL,'M',NULL,8,NULL,NULL,NULL,0.00000,NULL,0.00000,1,NULL),(179,2,348,NULL,NULL,'H076','绿色','L',NULL,8,NULL,NULL,NULL,0.00000,NULL,0.00000,1,NULL),(180,2,316,NULL,NULL,'1501-57','米色','I',NULL,8,NULL,'复4mm高丽棉(90密度蓝色) 丝印REFRESH商标橘白(距后跟20mm宽)',NULL,34.00000,0.02941,0.00000,1,NULL),(181,2,326,NULL,NULL,'116#','蓝色','S',NULL,9,NULL,'复1.0白切片+1.0膜+白定型布(2M/KG)(低温复合)(部件:1)   ',NULL,15.00000,0.06667,0.00000,1,NULL),(182,2,326,NULL,NULL,'116#','蓝色','S',NULL,9,NULL,'复1.2白切片 (低温复合)(部件:4)',NULL,28.30000,0.03534,0.00000,1,NULL),(183,2,326,NULL,NULL,'116#','蓝色','S',NULL,9,NULL,'复白细布 +2*3白布(低温复合)(部件:2.3)   ',NULL,11.30000,0.08850,0.00000,1,NULL),(184,2,326,NULL,NULL,'116#','蓝色','S',NULL,9,NULL,'嘉泰1501-57米 (低温复合)(部件:5)(康鸿激光)',NULL,150.00000,0.00667,0.00000,1,NULL),(185,2,316,NULL,NULL,'1501-57','米色','I',NULL,9,NULL,'上胶+PE纸',NULL,30.70000,0.03257,0.00000,1,NULL),(186,2,328,NULL,NULL,NULL,'红米','I',NULL,9,NULL,'复3mm白海绵+离子布',NULL,10.30000,0.09709,0.00000,1,NULL),(187,2,340,NULL,NULL,'1501-57','米色','A',NULL,9,'1.8*2.3折抽','对复(防爆)(刀冲)(需批搭地)  ',NULL,86.00000,0.01163,0.00000,1,NULL),(188,2,341,NULL,'Refresh',NULL,'古银色','A',NULL,9,NULL,'',NULL,0.50000,2.00000,0.00000,1,NULL),(189,2,342,NULL,'Refresh',NULL,'蓝色','A',NULL,9,'打码','',NULL,0.50000,2.00000,0.00000,1,NULL),(190,2,343,NULL,'Refresh',NULL,'古银色','A',NULL,9,NULL,'',NULL,0.50000,2.00000,0.00000,1,NULL),(191,2,344,NULL,NULL,'2227','米色','A',NULL,9,NULL,'',NULL,0.00000,0.00000,0.00000,1,NULL),(192,2,345,NULL,NULL,'H076','米黄色','O',NULL,9,'大底激光Refresh商标','',NULL,0.00000,NULL,0.00000,1,NULL),(193,2,347,NULL,NULL,'H076',NULL,'M',NULL,9,NULL,'',NULL,0.00000,NULL,0.00000,1,NULL),(194,2,348,NULL,NULL,'H076','绿色','L',NULL,9,NULL,'',NULL,0.00000,NULL,0.00000,1,NULL),(195,2,316,NULL,NULL,'1501-57','米色','I',NULL,9,NULL,'复4mm高丽棉(90密度蓝色) 丝印REFRESH商标橘白(距后跟20mm宽)',NULL,34.00000,0.02941,0.00000,1,NULL),(196,2,326,NULL,NULL,'116#','褐','S',NULL,10,NULL,'复1.0棕切片 +1.0膜+白定型布(2M/KG)(低温复合)(部件:1)      ',NULL,15.00000,0.06667,0.00000,1,NULL),(197,2,326,NULL,NULL,'116#','褐','S',NULL,10,NULL,'复1.2棕切片 (低温复合)(部件:4)',NULL,28.30000,0.03534,0.00000,1,NULL),(198,2,326,NULL,NULL,'116#','褐','S',NULL,10,NULL,'复白细布 +2*3白布(低温复合)(部件:2.3)   ',NULL,11.30000,0.08850,0.00000,1,NULL),(199,2,326,NULL,NULL,'116#','褐','S',NULL,10,NULL,'复嘉泰1501-57米 (低温复合)(部件:5)(康鸿激光)',NULL,150.00000,0.00667,0.00000,1,NULL),(200,2,316,NULL,NULL,'1501-57','米色','I',NULL,10,NULL,'上胶+PE纸',NULL,30.70000,0.03257,0.00000,1,NULL),(201,2,328,NULL,NULL,NULL,'红米','I',NULL,10,NULL,'复3mm白海绵+离子布',NULL,10.30000,0.09709,0.00000,1,NULL),(202,2,340,NULL,NULL,'1501-57','米色','A',NULL,10,'1.8*2.3折抽','对复(防爆)(刀冲)(需批搭地) ',NULL,86.00000,0.01163,0.00000,1,NULL),(203,2,341,NULL,'Refresh',NULL,'古银色','A',NULL,10,NULL,'',NULL,0.50000,2.00000,0.00000,1,NULL),(204,2,342,NULL,'Refresh',NULL,'褐色','A',NULL,10,'打码','',NULL,0.50000,2.00000,0.00000,1,NULL),(205,2,343,NULL,'Refresh',NULL,'古银色','A',NULL,10,NULL,'',NULL,0.50000,2.00000,0.00000,1,NULL),(206,2,344,NULL,NULL,'2445','米色','A',NULL,10,NULL,'',NULL,0.00000,0.00000,0.00000,1,NULL),(207,2,345,NULL,NULL,'H076','米黄色','O',NULL,10,'大底激光Refresh商标','',NULL,0.00000,NULL,0.00000,1,NULL),(208,2,347,NULL,NULL,'H076',NULL,'M',NULL,10,NULL,'',NULL,0.00000,NULL,0.00000,1,NULL),(209,2,348,NULL,NULL,'H076','绿色','L',NULL,10,NULL,'',NULL,0.00000,NULL,0.00000,1,NULL),(210,2,316,NULL,NULL,'1501-57','米色','I',NULL,10,NULL,'复4mm高丽棉(90密度蓝色) 丝印REFRESH商标橘白(距后跟20mm宽)',NULL,34.00000,0.02941,0.00000,1,NULL);
/*!40000 ALTER TABLE `craft_sheet_item` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer`
--

LOCK TABLES `customer` WRITE;
/*!40000 ALTER TABLE `customer` DISABLE KEYS */;
INSERT INTO `customer` VALUES (6,'62','CLOWSE'),(7,'06','CARNABI'),(9,'37','REFRESH'),(10,'37','XTI'),(11,'01','VIRUCCI');
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
  `bom_id` bigint NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `department`
--

LOCK TABLES `department` WRITE;
/*!40000 ALTER TABLE `department` DISABLE KEYS */;
INSERT INTO `department` VALUES (1,'裁断工段'),(2,'针车工段'),(3,'成型工段'),(4,'生产部'),(5,'技术部'),(6,'物控部'),(7,'行政部'),(8,'总经理'),(9,'人事部'),(10,'业务部'),(11,'开发一部'),(12,'总仓'),(13,'财务部'),(14,'开发二部'),(15,'开发三部'),(16,'开发四部');
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
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `finished_estimated_amount` int NOT NULL DEFAULT (_utf8mb4'0'),
  `finished_amount` int NOT NULL DEFAULT '0',
  `finished_status` tinyint DEFAULT NULL COMMENT '0：未入库\n1：已入库\n2：已出库',
  `current_revenue` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`finished_shoe_id`),
  UNIQUE KEY `unq_finished_shoe_storage` (`order_shoe_type_id`),
  KEY `fk_finished_shoe_storage` (`order_shoe_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `material_type_id` int NOT NULL DEFAULT '1',
  `material_category` int DEFAULT '0',
  PRIMARY KEY (`material_id`),
  UNIQUE KEY `unq_material` (`material_supplier`,`material_name`)
) ENGINE=InnoDB AUTO_INCREMENT=362 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `material`
--

LOCK TABLES `material` WRITE;
/*!40000 ALTER TABLE `material` DISABLE KEYS */;
INSERT INTO `material` VALUES (1,'采购革','米','2024-09-07',1,1,0),(2,'真皮','米','2024-09-07',1,1,0),(3,'羊筋绒','米','2024-09-07',1,1,0),(4,'瑞佳','米','2024-09-07',30,1,0),(5,'宝社','米','2024-09-07',31,1,0),(6,'鸿运','米','2024-09-07',207,1,0),(7,'润丰','米','2024-09-07',59,1,0),(8,'鸿源','米','2024-09-07',63,1,0),(9,'真皮绒','米','2024-09-07',1,1,0),(10,'唯佳','米','2024-09-07',62,1,0),(11,'国茂','米','2024-09-07',70,1,0),(12,'深源','米','2024-09-07',81,1,0),(13,'添鸿','米','2024-09-07',83,1,0),(14,'瓯瑞','米','2024-09-07',86,1,0),(15,'贴皮','米','2024-09-07',1,1,0),(16,'PU里','米','2024-09-07',1,2,0),(17,'几皮里','米','2024-09-07',1,2,0),(18,'布里','米','2024-09-07',1,2,0),(19,'毛里','米','2024-09-07',1,2,0),(20,'拉毛布','米','2024-09-07',1,2,0),(21,'定型布','米','2024-09-07',1,2,0),(22,'鞋眼衬','米','2024-09-07',1,2,0),(23,'海绵-张','张','2024-09-07',1,2,0),(24,'海绵-米','米','2024-09-07',1,2,0),(25,'猪皮里','尺','2024-09-07',1,2,0),(26,'乳胶-件','件','2024-09-07',1,2,0),(27,'PE纸','件','2024-09-07',1,2,0),(28,'海绵条','条','2024-09-07',1,2,0),(29,'内衬','米','2024-09-07',1,2,0),(30,'乳胶-米','米','2024-09-07',1,2,0),(31,'高丽棉-米','米','2024-09-07',1,2,0),(32,'上线','个','2024-09-07',1,3,0),(33,'下线','个','2024-09-07',1,3,0),(34,'蜡线','斤','2024-09-07',1,3,0),(35,'空心线','个','2024-09-07',1,3,0),(36,'双面胶','件','2024-09-07',1,3,0),(37,'美纹纸','件','2024-09-07',1,3,0),(38,'编织袋','条','2024-09-07',1,3,0),(39,'保险丝','个','2024-09-07',1,3,0),(40,'压缝条','盘','2024-09-07',1,3,0),(41,'补强带','件','2024-09-07',1,3,0),(42,'保险条','盘','2024-09-07',1,3,0),(43,'牛皮纸','件','2024-09-07',1,3,0),(44,'珠光线','个','2024-09-07',1,3,0),(45,'胶水','公斤','2024-09-07',1,4,0),(46,'处理剂','公斤','2024-09-07',1,4,0),(47,'固化剂','瓶','2024-09-07',1,4,0),(48,'鞋面油漆','公斤','2024-09-07',1,4,0),(49,'鞋面蜡水','公斤','2024-09-07',1,4,0),(50,'清洁剂','公斤','2024-09-07',1,4,0),(51,'改色剂','公斤','2024-09-07',1,4,0),(52,'巴西蜡','块','2024-09-07',1,4,0),(53,'粉胶-桶','桶','2024-09-07',1,4,0),(54,'喷胶','公斤','2024-09-07',1,4,0),(55,'黑膏','瓶','2024-09-07',1,4,0),(56,'白胶','公斤','2024-09-07',1,4,0),(57,'去胶剂','公斤','2024-09-07',1,4,0),(58,'处理剂-壶','壶','2024-09-07',1,4,0),(59,'鞋油','公斤','2024-09-07',1,4,0),(60,'硫化剂','瓶','2024-09-07',1,4,0),(61,'补伤膏','公斤','2024-09-07',1,4,0),(62,'烧焦蜡','块','2024-09-07',1,4,0),(63,'鞋面蜡油','公斤','2024-09-07',1,4,0),(64,'包头水','公斤','2024-09-07',1,4,0),(65,'渗透剂','瓶','2024-09-07',1,4,0),(66,'填充蜡','块','2024-09-07',1,4,0),(67,'雾蜡剂','公斤','2024-09-07',1,4,0),(68,'擦色蜡','块','2024-09-07',1,4,0),(69,'皮胚浓缩蜡液','公斤','2024-09-07',1,4,0),(70,'抛光蜡','条','2024-09-07',1,4,0),(71,'处理剂-瓶','瓶','2024-09-07',1,4,0),(72,'修补膏','公斤','2024-09-07',1,4,0),(73,'封口胶','瓶','2024-09-07',1,4,0),(74,'饰扣-双','双','2024-09-07',1,5,0),(75,'饰扣-套','套','2024-09-07',1,5,0),(76,'小饰扣-斤','斤','2024-09-07',1,5,0),(77,'小饰扣-包','包','2024-09-07',1,5,0),(78,'鞋眼-斤','斤','2024-09-07',1,5,0),(79,'鞋眼-包/万','包','2024-09-07',1,5,0),(80,'鞋眼垫片-斤','斤','2024-09-07',1,5,0),(81,'帽钉-斤','斤','2024-09-07',1,5,0),(82,'帽钉-包','包','2024-09-07',1,5,0),(83,'尼龙拉链-双','双','2024-09-07',1,5,0),(84,'尼龙拉链-条','条','2024-09-07',1,5,0),(85,'金属拉链-双','双','2024-09-07',1,5,0),(86,'金属拉链-条','条','2024-09-07',1,5,0),(87,'拉链头-双','双','2024-09-07',1,5,0),(88,'拉链头-个','个','2024-09-07',1,5,0),(89,'鞋带-双','双','2024-09-07',1,5,0),(90,'松紧-米','米','2024-09-07',1,5,0),(91,'松紧-盘','盘','2024-09-07',1,5,0),(92,'织带-米','米','2024-09-07',1,5,0),(93,'织带-盘','盘','2024-09-07',1,5,0),(94,'毛刺-米','米','2024-09-07',1,5,0),(95,'毛刺-盘','盘','2024-09-07',1,5,0),(96,'皮标','双','2024-09-07',1,5,0),(97,'布标','双','2024-09-07',1,5,0),(98,'鞋眼-套','套','2024-09-07',1,5,0),(99,'帽钉-颗','颗','2024-09-07',1,5,0),(100,'布标-片','张','2024-09-07',1,5,0),(101,'鞋眼垫片-颗','颗','2024-09-07',1,5,0),(102,'穿花条','米','2024-09-07',1,5,0),(103,'鞋盒','个','2024-09-07',1,6,0),(104,'隔板','张','2024-09-07',1,6,0),(105,'脚模','双','2024-09-07',1,6,0),(106,'泡沫筒衬','双','2024-09-07',1,6,0),(107,'纸筒衬','双','2024-09-07',1,6,0),(108,'鞋盒加工','个','2024-09-07',1,6,0),(109,'双面玖龙双瓦外箱','个','2024-09-07',1,6,0),(110,'海王B级双瓦外箱','个','2024-09-07',1,6,0),(111,'拷贝纸','张','2024-09-07',1,6,0),(112,'塞纸','件','2024-09-07',1,6,0),(113,'贴标','套','2024-09-07',1,6,0),(114,'包装袋','双','2024-09-07',1,6,0),(115,'防霉片','张','2024-09-07',1,6,0),(116,'胶带纸','卷','2024-09-07',1,6,0),(117,'铜板纸','卷','2024-09-07',1,6,0),(118,'碳带','卷','2024-09-07',1,6,0),(119,'吊牌','个','2024-09-07',1,6,0),(120,'B级双瓦外箱','个','2024-09-07',1,6,0),(121,'干燥剂','包','2024-09-07',1,6,0),(122,'特一双瓦外箱','个','2024-09-07',1,6,0),(123,'白板双瓦外箱','个','2024-09-07',1,6,0),(124,'B级单瓦外箱','个','2024-09-07',1,6,0),(125,'纸筒管','个','2024-09-07',1,6,0),(126,'防霉纸','张','2024-09-07',1,6,0),(127,'海王B级双瓦垫片','个','2024-09-07',1,6,0),(128,'B级单瓦垫片','个','2024-09-07',1,6,0),(129,'B级双瓦垫片','个','2024-09-07',1,6,0),(130,'特殊白板双瓦外箱','个','2024-09-07',1,6,0),(131,'泡沫棒','双','2024-09-07',1,6,0),(132,'双瓦垫片','个','2024-09-07',1,6,0),(133,'美牛双瓦外箱','个','2024-09-07',1,6,0),(134,'打包带','卷','2024-09-07',1,6,0),(135,'纸衬','双','2024-09-07',1,6,0),(136,'美牛双瓦垫片','个','2024-09-07',1,6,0),(137,'小帆船外箱','个','2024-09-07',1,6,0),(138,'大底','双','2024-09-07',1,7,1),(139,'中底','双','2024-09-07',1,7,1),(140,'鞋跟','双','2024-09-07',1,7,0),(141,'底片','双','2024-09-07',1,7,0),(142,'出面','双','2024-09-07',1,7,0),(143,'内增高','双','2024-09-07',1,7,0),(144,'中底板','张','2024-09-07',1,7,0),(145,'防水台','张','2024-09-07',1,7,0),(146,'中底卡纸','双','2024-09-07',1,7,0),(147,'其他工具','件','2024-09-07',1,8,0),(148,'剪刀','把','2024-09-07',1,8,0),(149,'手套','件','2024-09-07',1,8,0),(150,'刷子','把','2024-09-07',1,8,0),(151,'口罩','件','2024-09-07',1,8,0),(152,'针筒','件','2024-09-07',1,8,0),(153,'白碎布','斤','2024-09-07',1,8,0),(154,'背心袋','件','2024-09-07',1,8,0),(155,'尼龙绳','斤','2024-09-07',1,8,0),(156,'橡皮筋','斤','2024-09-07',1,8,0),(157,'擦胶皮','件','2024-09-07',1,8,0),(158,'胶油壶','个','2024-09-07',1,8,0),(159,'记号笔','件','2024-09-07',1,8,0),(160,'砂轮纸','件','2024-09-07',1,8,0),(161,'清洗笔','件','2024-09-07',1,8,0),(162,'707胶','件','2024-09-07',1,8,0),(163,'装跟钉','件','2024-09-07',1,8,0),(164,'垫芯','件','2024-09-07',1,8,0),(165,'复0.6切片','米','2024-09-07',1,9,0),(166,'复0.6棕白切片','米','2024-09-07',1,9,0),(167,'复0.8切片','米','2024-09-07',1,9,0),(168,'复0.8棕白切片','米','2024-09-07',1,9,0),(169,'复1.0切片','米','2024-09-07',1,9,0),(170,'复1.0棕白切片','米','2024-09-07',1,9,0),(171,'复1.1切片','米','2024-09-07',1,9,0),(172,'复1.1棕白切片','米','2024-09-07',1,9,0),(173,'复1.2切片','米','2024-09-07',1,9,0),(174,'复1.2棕白切片','米','2024-09-07',1,9,0),(175,'复1.5切片','米','2024-09-07',1,9,0),(176,'复1.5棕白切片','米','2024-09-07',1,9,0),(177,'复2*1布','米','2024-09-07',1,9,0),(178,'复2*3布','米','2024-09-07',1,9,0),(179,'复PU里','米','2024-09-07',1,9,0),(180,'复几皮里','米','2024-09-07',1,9,0),(181,'复超纤里','米','2024-09-07',1,9,0),(182,'复佳积布','米','2024-09-07',1,9,0),(183,'复定型布','米','2024-09-07',1,9,0),(184,'复0.2海绵+里子布','米','2024-09-07',1,9,0),(185,'复0.3海绵+里子布','米','2024-09-07',1,9,0),(186,'复0.4海绵+里子布','米','2024-09-07',1,9,0),(187,'复2.0回力胶','米','2024-09-07',1,9,0),(188,'复3.0回力胶','米','2024-09-07',1,9,0),(189,'复3.0乳胶','米','2024-09-07',1,9,0),(190,'对复','米','2024-09-07',1,9,0),(191,'两边细布中间+PE纸','米','2024-09-07',1,9,0),(192,'上胶+PE纸','米','2024-09-07',1,9,0),(193,'复细布','米','2024-09-07',1,9,0),(194,'复无纺布','米','2024-09-07',1,9,0),(195,'复1.0切片+1.0膜+定型布','米','2024-09-07',1,9,0),(196,'复2*3布上胶+PE纸','米','2024-09-07',1,9,0),(197,'复1.0切片+定型布','米','2024-09-07',1,9,0),(198,'复3.0记忆海绵+2.0乳胶','米','2024-09-07',1,9,0),(199,'复0.6切片+PU里','米','2024-09-07',1,9,0),(200,'复5.0记忆海绵+无纺布','米','2024-09-07',1,9,0),(201,'复细布+2*3布','米','2024-09-07',1,9,0),(202,'复8N布','米','2024-09-07',1,9,0),(203,'复无纺布+3.0回力胶','米','2024-09-07',1,9,0),(204,'复2*3布+定型布','米','2024-09-07',1,9,0),(205,'复2*1布+2*3布','米','2024-09-07',1,9,0),(206,'复0.6切片+PE纸','米','2024-09-07',1,9,0),(207,'复细布+1.5切片','米','2024-09-07',1,9,0),(208,'复佳积布+2*3布','米','2024-09-07',1,9,0),(209,'复18磅布上防脱纱','米','2024-09-07',1,9,0),(210,'复1.2切片+定型布','米','2024-09-07',1,9,0),(211,'复细布+2*3布*定型布','米','2024-09-07',1,9,0),(212,'复0.3海绵','米','2024-09-07',1,9,0),(213,'复拉毛布上胶+PE纸','米','2024-09-07',1,9,0),(214,'复无纺布上胶+PE纸','米','2024-09-07',1,9,0),(215,'复1.0切片+PU里','米','2024-09-07',1,9,0),(216,'复14磅布','米','2024-09-07',1,9,0),(217,'复佳积布+2*1布','米','2024-09-07',1,9,0),(218,'复佳积布上胶+PE纸','米','2024-09-07',1,9,0),(219,'复2*3布+PU里','米','2024-09-07',1,9,0),(220,'复18磅布+2*1布','米','2024-09-07',1,9,0),(221,'复拉毛布','米','2024-09-07',1,9,0),(222,'复无纺布+羊筋绒','米','2024-09-07',1,9,0),(223,'复佳积布+1.2切片','米','2024-09-07',1,9,0),(224,'复1.0切片+1.0膜+定型布复PU里','米','2024-09-07',1,9,0),(225,'复细布+1.2切片','米','2024-09-07',1,9,0),(226,'复0.8切片加网','米','2024-09-07',1,9,0),(227,'复0.5海绵','米','2024-09-07',1,9,0),(228,'复细布+1.0切片','米','2024-09-07',1,9,0),(229,'复1.2切片+1.0膜+定型布','米','2024-09-07',1,9,0),(230,'复细布+2*3布+PU里','米','2024-09-07',1,9,0),(231,'复0.3海绵+无纺布','米','2024-09-07',1,9,0),(232,'复2*1布+2*3布+定型布','米','2024-09-07',1,9,0),(233,'复0.5海绵+3.0回力胶+特克松','米','2024-09-07',1,9,0),(234,'复0.5海绵+里子布','米','2024-09-07',1,9,0),(235,'复里子布','米','2024-09-07',1,9,0),(236,'复3.0高力棉','米','2024-09-07',1,9,0),(237,'复5.5大力棉+1.0EVA','米','2024-09-07',1,9,0),(238,'复2*1布+2*3布+超纤布','米','2024-09-07',1,9,0),(239,'复2*1布上胶+PE纸','米','2024-09-07',1,9,0),(240,'复0.5海绵+无纺布','米','2024-09-07',1,9,0),(241,'复2*1布+2*3布+帆布','米','2024-09-07',1,9,0),(242,'复1.0切片上胶+PE纸','米','2024-09-07',1,9,0),(243,'复佳积布+无纺布','米','2024-09-07',1,9,0),(244,'复3.0记忆海绵','米','2024-09-07',1,9,0),(245,'复无纺布+PU里','米','2024-09-07',1,9,0),(246,'复2*3布+无纺布','米','2024-09-07',1,9,0),(247,'复2*3布+细布','米','2024-09-07',1,9,0),(248,'复细布+佳积布','米','2024-09-07',1,9,0),(249,'复2*3布+超纤布','米','2024-09-07',1,9,0),(250,'复细布+2*3布+超纤布','米','2024-09-07',1,9,0),(251,'复0.6海绵+无纺布','米','2024-09-07',1,9,0),(252,'复空心棉','米','2024-09-07',1,9,0),(253,'复2*3布+拉毛布','米','2024-09-07',1,9,0),(254,'复4.0乳胶','米','2024-09-07',1,9,0),(255,'复佳积布+0.3海绵+里子布','米','2024-09-07',1,9,0),(256,'复无纺布+3.0高力棉','米','2024-09-07',1,9,0),(257,'复佳积布+0.2海绵+里子布','米','2024-09-07',1,9,0),(258,'复0.8EVA','米','2024-09-07',1,9,0),(259,'复无纺布+高力棉','米','2024-09-07',1,9,0),(260,'复高力棉','米','2024-09-07',1,9,0),(261,'复2*1布+定型布','米','2024-09-07',1,9,0),(262,'复2*1布+2*3布+无纺布','米','2024-09-07',1,9,0),(263,'复防爆胶','米','2024-09-07',1,9,0),(264,'复4*3布+无纺布','米','2024-09-07',1,9,0),(265,'复无纺布+0.5海绵+无纺布','米','2024-09-07',1,9,0),(266,'复细布+1.2切片+PU里','米','2024-09-07',1,9,0),(267,'复2*1布+无纺布','米','2024-09-07',1,9,0),(268,'复2*3布+定型布+无纺布','米','2024-09-07',1,9,0),(269,'复2*3布+膜+定型布复PU里','米','2024-09-07',1,9,0),(270,'复4*3布','米','2024-09-07',1,9,0),(271,'复5.0记忆海绵','米','2024-09-07',1,9,0),(272,'复1.5SBR+里子布','米','2024-09-07',1,9,0),(273,'复细布上胶+PE纸','米','2024-09-07',1,9,0),(274,'0.8切片复细布上胶+PE纸','米','2024-09-07',1,9,0),(275,'加工费-米','双','2024-09-07',1,10,0),(276,'加工费-双','双','2024-09-07',1,10,0),(277,'加工费-件','双','2024-09-07',1,10,0),(278,'加工费-盘','双','2024-09-07',1,10,0),(279,'加工费-次','双','2024-09-07',1,10,0),(280,'成型烫加工','双','2024-09-07',1,10,0),(281,'全烫加工','双','2024-09-07',1,10,0),(282,'热熔胶-双','双','2024-09-07',1,10,0),(283,'飞织加工','双','2024-09-07',1,10,0),(284,'刀模-支','双','2024-09-07',1,10,0),(285,'刀模-套','双','2024-09-07',1,10,0),(286,'男单','双','2024-09-07',1,11,0),(287,'男棉','双','2024-09-07',1,11,0),(288,'男高棉','双','2024-09-07',1,11,0),(289,'女单','双','2024-09-07',1,11,0),(290,'女棉','双','2024-09-07',1,11,0),(291,'女高棉','双','2024-09-07',1,11,0),(292,'楦头加工','双','2024-09-07',1,11,0),(293,'女二棉','双','2024-09-07',1,11,0),(294,'男二棉','双','2024-09-07',1,11,0),(295,'男单棉','双','2024-09-07',1,11,0),(296,'维修费','次','2024-09-07',1,12,0),(297,'零配件','件','2024-09-07',1,12,0),(298,'机器设备','件','2024-09-07',1,12,0),(299,'办公设备','件','2024-09-07',1,12,0),(300,'洗洁精','斤','2024-09-07',1,12,0),(301,'后勤用品','件','2024-09-07',1,12,0),(302,'柴油','斤','2024-09-07',1,12,0),(303,'办公用品','件','2024-09-07',1,12,0),(304,'医疗用品','件','2024-09-07',1,12,0),(305,'液压油','桶','2024-09-07',1,12,0),(306,'开发样品','件','2024-09-07',1,13,0),(307,'样品-米','米','2024-09-07',1,13,0),(308,'样品-件','件','2024-09-07',1,13,0),(309,'样品-套','套','2024-09-07',1,13,0),(310,'开发工具','件','2024-09-07',1,13,0),(311,'样品皮-尺','尺','2024-09-07',1,13,0),(312,'样品-双','双','2024-09-07',1,13,0),(313,'莱卡布','米','2024-11-01',36,1,0),(314,'弹力布','米','2024-11-01',1,2,0),(315,'网布','米','2024-11-01',1,2,0),(316,'PU里','米','2024-11-01',29,2,0),(317,'中底','双','2024-11-01',208,7,0),(318,'大底','对','2024-11-06',33,7,1),(319,'嘉泰','米','2024-11-06',29,2,0),(320,'佳织布','米','2024-11-06',1,2,0),(321,'森达','个','2024-11-06',6,12,1),(322,'中底','对','2024-11-06',130,7,1),(323,'拉链','个','2024-11-24',1,3,0),(324,'饰扣','个','2024-11-24',1,3,0),(325,'高丽棉','双','2024-11-24',1,9,0),(326,'羊筋绒','米','2024-12-04',36,1,0),(327,'黑褪灰色毛','米','2024-12-04',209,1,0),(328,'佳积布','米','2024-12-04',72,2,0),(329,'商标圆扣','个','2024-12-04',57,3,0),(330,'尼龙拉链','条','2024-12-04',210,3,0),(331,'商标拉头','个','2024-12-04',210,3,0),(332,'圆棉带','条','2024-12-04',43,3,0),(333,'TPR','对','2024-12-04',33,7,1),(334,'化纤板/普钢/T板','对','2024-12-04',5,7,1),(335,'B级','对','2024-12-04',6,12,1),(336,'','','2024-12-04',211,1,0),(337,'PU','米','2024-12-04',212,1,0),(338,'PU里','米','2024-12-04',213,2,0),(339,'佳积布','米','2024-12-05',211,2,0),(340,'拉链皮','米','2024-12-05',29,3,0),(341,'圆标扣','个','2024-12-05',214,3,0),(342,'尼龙拉链','条','2024-12-05',215,3,0),(343,'商标拉链头','个','2024-12-05',215,3,0),(344,'210*3车线','个','2024-12-05',19,3,0),(345,'TPR','对','2024-12-05',216,7,1),(346,'2.0蓝板/锰钢+化纤','对','2024-12-05',217,7,1),(347,'蓝板/锰钢/化纤','对','2024-12-05',5,7,1),(348,'B级','对','2024-12-05',218,12,1),(349,'P-U','','2024-12-05',62,1,0),(350,'PU','','2024-12-05',62,1,0),(351,'弹力布','','2024-12-05',2,2,0),(352,'格子布','','2024-12-05',2,2,0),(353,'300#鞋眼','','2024-12-05',210,3,0),(354,'圆打蜡带','','2024-12-05',219,3,0),(355,'TPR','','2024-12-05',220,7,1),(356,'化纤板/猛钢/红板','','2024-12-05',208,7,1),(357,'23057x','','2024-12-05',7,12,1),(358,'嘉泰','','2024-12-05',191,9,0),(359,'PU里','','2024-12-05',221,2,0),(360,'2.0圆打蜡带','','2024-12-05',43,3,0),(361,'羊筋绒复1.0棕切片+1.0膜+白定型布','米','2024-12-13',189,9,0);
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
  `order_id` bigint DEFAULT NULL,
  `order_shoe_id` bigint DEFAULT NULL,
  `material_id` bigint NOT NULL,
  `estimated_inbound_amount` decimal(10,5) DEFAULT '0.00000',
  `actual_inbound_amount` decimal(10,5) DEFAULT '0.00000',
  `current_amount` decimal(10,5) NOT NULL DEFAULT (0),
  `unit_price` decimal(10,2) DEFAULT NULL,
  `material_specification` varchar(40) DEFAULT '',
  `material_outsource_status` tinyint NOT NULL DEFAULT '0',
  `material_outsource_outbound_date` date DEFAULT NULL,
  `material_storage_color` varchar(40) DEFAULT '',
  `purchase_divide_order_id` bigint DEFAULT NULL,
  `material_estimated_arrival_date` date DEFAULT NULL,
  `material_model` varchar(40) DEFAULT '',
  `material_storage_status` tinyint DEFAULT (_utf8mb4'0') COMMENT '0：未完成入库\n1：已完成入库\n2：已完成出库',
  `composite_unit_cost` decimal(10,2) DEFAULT NULL,
  `craft_name` varchar(200) DEFAULT NULL,
  `department_id` int DEFAULT NULL,
  `production_instruction_item_id` bigint DEFAULT NULL,
  PRIMARY KEY (`material_storage_id`),
  UNIQUE KEY `unq_material_storage` (`material_id`,`order_shoe_id`,`material_storage_color`),
  KEY `fk_material_storage` (`order_shoe_id`),
  KEY `fk_material_storage_materials` (`material_id`),
  KEY `fk_material_storage_color` (`material_storage_color`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `material_storage`
--

LOCK TABLES `material_storage` WRITE;
/*!40000 ALTER TABLE `material_storage` DISABLE KEYS */;
INSERT INTO `material_storage` VALUES (1,1,5,326,29.00000,29.00000,19.00000,20.50,'',0,NULL,'黑',1,NULL,'',1,NULL,'复1.0棕切片+1.0膜+白定型布@复1.2棕切片@复100K驼无纺布',NULL,NULL),(2,1,5,316,11.00000,0.00000,0.00000,0.00,'',0,NULL,'黑',2,NULL,'1501-1',0,NULL,'折抽18/23mm宽',NULL,NULL),(3,1,5,328,40.00000,0.00000,0.00000,0.00,'',0,NULL,'黑',4,NULL,'',0,NULL,'复3mm黑海绵+离子布',NULL,NULL),(4,1,5,329,476.00000,0.00000,0.00000,0.00,'REFRESH',0,NULL,'古银',5,NULL,'',0,NULL,NULL,NULL,NULL),(5,1,5,332,476.00000,0.00000,0.00000,0.00,'',0,NULL,'黑',7,NULL,'',0,NULL,NULL,NULL,NULL),(6,1,5,327,7.00000,0.00000,0.00000,0.00,'',0,NULL,'黑灰',8,NULL,'',0,NULL,'复50K驼无纺布',NULL,NULL),(7,1,5,330,476.00000,0.00000,0.00000,0.00,'',0,NULL,'黑',10,NULL,'',0,NULL,NULL,NULL,NULL),(8,1,5,331,476.00000,0.00000,0.00000,0.00,'REFRESH',0,NULL,'古银',10,NULL,'',0,NULL,NULL,NULL,NULL),(9,1,5,361,10.00000,0.00000,0.00000,NULL,'',0,NULL,'黑',NULL,NULL,'',0,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `material_storage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `material_type`
--

DROP TABLE IF EXISTS `material_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `material_type` (
  `material_type_id` int NOT NULL AUTO_INCREMENT,
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
INSERT INTO `operation` VALUES (0,'Type-1-test-0',1,0,1),(1,'Type-1-test-1',1,0,2),(2,'Type-1-test-2',1,1,1),(3,'Type-1-test-3',1,1,2),(4,'Type-1-test-4',1,2,1),(5,'Type-1-test-5',1,2,2),(6,'Type-1-test-6',1,3,1),(7,'Type-1-test-7',1,3,2),(8,'Type-1-test-8',1,4,1),(9,'Type-1-test-9',1,4,2),(10,'Type-1-test-10',1,5,1),(11,'Type-1-test-11',1,5,2),(12,'Type-1-test-12',1,6,1),(13,'Type-1-test-13',1,6,2),(14,'Type-1-test-14',1,7,1),(15,'总经理确认完成',1,7,2),(16,'Type-1-test-16',1,8,1),(17,'生产副总确认完成-测',1,8,2),(18,'Type-1-test-18',1,9,1),(19,'Type-1-test-19',1,9,2),(20,'Type-1-test-20',1,10,1),(21,'Type-1-test-21',1,10,2),(22,'Type-1-test-22',1,11,1),(23,'Type-1-test-23',1,11,2),(24,'Type-1-test-24',1,12,1),(25,'Type-1-test-25',1,12,2),(26,'Type-1-test-26',1,13,1),(27,'Type-1-test-27',1,13,2),(28,'Type-1-test-28',1,14,1),(29,'Type-1-test-29',1,14,2),(30,'Type-1-test-30',1,15,1),(31,'Type-1-test-31',1,15,2),(32,'Type-1-test-32',1,16,1),(33,'Type-1-test-33',1,16,2),(34,'Type-1-test-34',1,17,1),(35,'Type-1-test-35',1,17,2),(36,'Type-1-test-36',1,18,1),(37,'Type-1-test-37',1,18,2),(38,'Type-2-test-0',2,0,1),(39,'投产指令单下发完成',2,0,2),(40,'Type-2-test-2',2,1,1),(41,'Type-2-test-3',2,1,2),(42,'Type-2-test-4',2,2,1),(43,'Type-2-test-5',2,2,2),(44,'Type-2-test-6',2,3,1),(45,'Type-2-test-7',2,3,2),(46,'Type-2-test-8',2,4,1),(47,'Type-2-test-9',2,4,2),(48,'Type-2-test-10',2,5,1),(49,'Type-2-test-11',2,5,2),(50,'Type-2-test-12',2,6,1),(51,'Type-2-test-13',2,6,2),(52,'Type-2-test-14',2,7,1),(53,'Type-2-test-15',2,7,2),(54,'Type-2-test-16',2,8,1),(55,'Type-2-test-17',2,8,2),(56,'Type-2-test-18',2,9,1),(57,'Type-2-test-19',2,9,2),(58,'Type-2-test-20',2,10,1),(59,'Type-2-test-21',2,10,2),(60,'Type-2-test-22',2,11,1),(61,'Type-2-test-23',2,11,2),(62,'Type-2-test-24',2,12,1),(63,'Type-2-test-25',2,12,2),(64,'Type-2-test-26',2,13,1),(65,'Type-2-test-27',2,13,2),(66,'Type-2-test-28',2,14,1),(67,'Type-2-test-29',2,14,2),(68,'Type-2-test-30',2,15,1),(69,'Type-2-test-31',2,15,2),(70,'Type-2-test-32',2,16,1),(71,'Type-2-test-33',2,16,2),(72,'Type-2-test-34',2,17,1),(73,'Type-2-test-35',2,17,2),(74,'Type-2-test-36',2,18,1),(75,'Type-2-test-37',2,18,2),(76,'Type-2-test-38',2,19,1),(77,'Type-2-test-39',2,19,2),(78,'Type-2-test-40',2,20,1),(79,'Type-2-test-41',2,20,2),(80,'Type-2-test-42',2,21,1),(81,'Type-2-test-43',2,21,2),(82,'Type-2-test-44',2,22,1),(83,'Type-2-test-45',2,22,2),(84,'Type-2-test-46',2,23,1),(85,'Type-2-test-47',2,23,2),(86,'Type-2-test-48',2,24,1),(87,'Type-2-test-49',2,24,2),(88,'Type-2-test-50',2,25,1),(89,'Type-2-test-51',2,25,2),(90,'Type-2-test-52',2,26,1),(91,'Type-2-test-53',2,26,2),(92,'Type-2-test-54',2,27,1),(93,'Type-2-test-55',2,27,2),(94,'Type-2-test-56',2,28,1),(95,'Type-2-test-57',2,28,2),(96,'Type-2-test-58',2,29,1),(97,'Type-2-test-59',2,29,2),(98,'Type-2-test-60',2,30,1),(99,'Type-2-test-61',2,30,2),(100,'Type-2-test-62',2,31,1),(101,'Type-2-test-63',2,31,2),(102,'Type-2-test-64',2,32,1),(103,'Type-2-test-65',2,32,2),(104,'Type-2-test-66',2,33,1),(105,'Type-2-test-67',2,33,2),(106,'Type-2-test-68',2,34,1),(107,'Type-2-test-69',2,34,2),(108,'Type-2-test-70',2,35,1),(109,'Type-2-test-71',2,35,2),(110,'Type-2-test-72',2,36,1),(111,'Type-2-test-73',2,36,2),(112,'Type-2-test-74',2,37,1),(113,'Type-2-test-75',2,37,2),(114,'Type-2-test-76',2,38,1),(115,'Type-2-test-77',2,38,2),(116,'Type-2-test-78',2,39,1),(117,'Type-2-test-79',2,39,2),(118,'Type-2-test-80',2,40,1),(119,'Type-2-test-81',2,40,2),(120,'Type-2-test-82',2,41,1),(121,'Type-2-test-83',2,41,2),(122,'Type-2-test-84',2,42,1),(123,'Type-2-test-85',2,42,2);
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
  `batch_info_type_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `customer_id` int NOT NULL,
  `salesman_id` int NOT NULL,
  `production_list_upload_status` char(1) DEFAULT '0',
  `amount_list_upload_status` char(1) DEFAULT (0),
  `supervisor_id` int DEFAULT NULL,
  PRIMARY KEY (`order_id`),
  UNIQUE KEY `order_rid_UNIQUE` (`order_rid`),
  KEY `fk_orders_customers` (`customer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=71 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order`
--

LOCK TABLES `order` WRITE;
/*!40000 ALTER TABLE `order` DISABLE KEYS */;
INSERT INTO `order` VALUES (24,'W25-037','',21,'2025-01-03','2025-05-10',11,26,'2','0',10),(25,'W25-035','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(26,'W25-036','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(27,'W25-047','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(28,'W25-048','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(29,'W25-031','',22,'2025-01-03','2025-05-10',11,23,'2','0',10),(30,'W25-052','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(31,'W25-025','',22,'2025-01-03','2025-05-10',11,22,'2','0',10),(32,'W25-054','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(33,'W25-049','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(34,'W25-050','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(35,'W25-051','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(36,'W25-053','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(37,'W25-055','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(38,'W25-010','',22,'2025-01-03','2025-05-10',11,23,'2','0',10),(39,'W25-056','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(40,'W25-011','',22,'2025-01-03','2025-05-10',11,23,'2','0',10),(41,'W25-020','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(42,'W25-012','',22,'2025-01-03','2025-05-10',11,23,'2','0',10),(43,'W25-023','',22,'2025-01-03','2025-05-10',11,26,'2','0',10),(44,'W25-013','',22,'2025-01-03','2025-05-10',11,23,'2','0',10),(45,'W25-008','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(46,'W25-024','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(47,'W25-038','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(48,'W25-039','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(49,'W25-040','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(50,'W25-041','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(51,'W25-042','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(52,'W25-043','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(53,'W25-044','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(54,'W25-045','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(55,'W25-046','',22,'2025-01-04','2025-05-10',11,26,'2','0',10),(58,'K25-001','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(59,'K25-002','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(60,'K25-003','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(61,'K25-004','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(62,'K25-006','2114088 GRASSO',22,'2025-01-04','2025-03-15',10,26,'2','0',10),(63,'K25-007','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(64,'K25-008','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(65,'K25-009','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(66,'K25-010','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(67,'K25-012','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(68,'k25-011','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(69,'K25-013','2114090 GRASSO',22,'2025-01-04','2025-03-15',9,26,'2','0',10),(70,'K25-005','2114118 MKL',21,'2025-01-04','2025-04-20',10,26,'2','0',10);
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
) ENGINE=InnoDB AUTO_INCREMENT=66 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe`
--

LOCK TABLES `order_shoe` WRITE;
/*!40000 ALTER TABLE `order_shoe` DISABLE KEYS */;
INSERT INTO `order_shoe` VALUES (19,'','0','0','VRAE-90',24,57,'',''),(20,'','0','0','VRA-1061',25,58,'',''),(21,'','0','0','VRA-1062',26,59,'',''),(22,'','0','0','VR5-2058',27,61,'电绣取消',''),(23,'','0','0','VR5-2059',28,62,'',''),(24,'','0','0','VR5-2023',29,60,'',''),(25,'','0','0','VR5-2063',30,67,'',''),(26,'','0','0','VR5-2011',31,66,'',''),(27,'','0','0','VR5-2066',32,69,'头排电绣取消',''),(28,'','0','0','VR5-2060',33,63,'',''),(29,'','0','0','VR5-2061',34,64,'',''),(30,'','0','0','VR5-2062',35,65,'',''),(31,'','0','0','VR5-2065',36,68,'',''),(32,'','0','0','VR5-2067',37,71,'头排钻取消',''),(33,'','0','0','VR5-2025',38,70,'',''),(34,'','0','0','VR5-2068',39,73,'头排钻取消',''),(35,'','0','0','VR5-2026',40,72,'',''),(36,'','0','0','VR5-2008',41,74,'',''),(37,'','0','0','VR5-2027',42,75,'',''),(38,'','0','0','VR5-2007',43,76,'',''),(39,'','0','0','VR5-2028',44,77,'',''),(40,'','0','0','VR5-2009',45,79,'',''),(41,'','0','0','VR5-2010',46,80,'',''),(42,'','0','0','VR5-2038',47,81,'',''),(43,'','0','0','VR5-2039',48,82,'',''),(44,'','0','0','VR5-2050',49,83,'',''),(45,'','0','0','VR5-2051',50,84,'',''),(46,'','0','0','VR5-2052',51,85,'',''),(47,'','0','0','VR5-2053',52,86,'',''),(48,'','0','0','VR5-2055',53,87,'','铆钉改成V'),(49,'','0','0','VR5-2056',54,88,'',''),(50,'','0','0','VR5-2057',55,89,'',''),(53,'','0','0','170990',58,90,'','1.2111620 返单\n2.鞋底耐磨280'),(54,'','0','0','171977',59,52,'','1.2111620返单\n2.鞋底耐磨280'),(55,'','0','0','171981',60,91,'','1.2111620返单\n2.鞋底耐磨280'),(56,'','0','0','171985',61,92,'','1.2111622返单\n2.鞋底耐磨280'),(57,'','0','0','143367',62,93,'','1.2111622返单\n2.鞋底耐磨280'),(58,'','0','0','170997',63,94,'','1.2111620返单\n2.鞋底耐磨280'),(59,'','0','0','171000',64,49,'','1.2111620返单\n2.鞋底耐磨280'),(60,'','0','0','171009',65,51,'','1.2111620返单\n2.鞋底耐磨280'),(61,'','0','0','172125',66,54,'','1.2111620返单\n2.鞋底耐磨280'),(62,'','0','0','171993',67,96,'','1.2111620 返单\n2.鞋底耐磨280'),(63,'','0','0','171994',68,95,'','1.2111620返单\n2.鞋底耐磨280'),(64,'','0','0','171002',69,50,'','1.2111620返单\n2.鞋底耐磨280'),(65,'','0','0','144510',70,17,'1.小脚趾位置楦头加一点，前后热熔胶太硬，大底需减重','1.鞋底耐磨280');
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
) ENGINE=InnoDB AUTO_INCREMENT=200 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_batch_info`
--

LOCK TABLES `order_shoe_batch_info` WRITE;
/*!40000 ALTER TABLE `order_shoe_batch_info` DISABLE KEYS */;
INSERT INTO `order_shoe_batch_info` VALUES (1,'C12A',84,0,0,0,0,0,0,7,14,21,21,14,7,0,1,9.30,781.20,'',66,7),(2,'C12A',84,0,0,0,0,0,0,7,14,21,21,14,7,0,2,9.30,781.20,'',66,7),(10,'7.5单码',12,0,12,0,0,0,0,0,0,0,0,0,0,0,4,0.00,0.00,'',34,1),(11,'8单码',12,0,0,12,0,0,0,0,0,0,0,0,0,0,4,0.00,0.00,'',35,1),(12,'8.5单码',12,0,0,0,12,0,0,0,0,0,0,0,0,0,4,0.00,0.00,'',36,1),(13,'9单码',12,0,0,0,0,12,0,0,0,0,0,0,0,0,4,0.00,0.00,'',37,1),(14,'9.5单码',12,0,0,0,0,0,12,0,0,0,0,0,0,0,4,0.00,0.00,'',39,1),(15,'10单码',24,0,0,0,0,0,0,24,0,0,0,0,0,0,4,0.00,0.00,'',40,2),(16,'10.5单码',48,0,0,0,0,0,0,0,48,0,0,0,0,0,4,0.00,0.00,'',42,4),(17,'11单码',48,0,0,0,0,0,0,0,0,48,0,0,0,0,4,0.00,0.00,'',44,4),(18,'12单码',48,0,0,0,0,0,0,0,0,0,0,48,0,0,4,0.00,0.00,'',52,4),(19,'13单码',36,0,0,0,0,0,0,0,0,0,0,0,0,36,4,0.00,0.00,'',55,3),(20,'7单码',12,12,0,0,0,0,0,0,0,0,0,0,0,0,5,0.00,0.00,'',64,1),(21,'7.5单码',12,0,12,0,0,0,0,0,0,0,0,0,0,0,5,0.00,0.00,'',34,1),(22,'8单码',12,0,0,12,0,0,0,0,0,0,0,0,0,0,5,0.00,0.00,'',35,1),(23,'8.5单码',48,0,0,0,48,0,0,0,0,0,0,0,0,0,5,0.00,0.00,'',36,4),(24,'9.5单码',12,0,0,0,0,0,12,0,0,0,0,0,0,0,5,0.00,0.00,'',39,1),(25,'10单码',12,0,0,0,0,0,0,12,0,0,0,0,0,0,5,0.00,0.00,'',40,1),(26,'10.5单码',48,0,0,0,0,0,0,0,48,0,0,0,0,0,5,0.00,0.00,'',42,4),(27,'11单码',12,0,0,0,0,0,0,0,0,12,0,0,0,0,5,0.00,0.00,'',44,1),(28,'12单码',12,0,0,0,0,0,0,0,0,0,0,12,0,0,5,0.00,0.00,'',52,1),(29,'13单码',24,0,0,0,0,0,0,0,0,0,0,0,0,24,5,0.00,0.00,'',55,2),(30,'S12A',132,0,0,11,22,33,33,22,11,0,0,0,0,0,6,0.00,0.00,'',54,11),(31,'S12B',24,0,2,4,6,6,4,2,0,0,0,0,0,0,6,0.00,0.00,'',56,2),(32,'S6A1',12,0,0,2,2,2,2,2,2,0,0,0,0,0,6,0.00,0.00,'',57,2),(33,'S6A2',6,0,0,0,1,2,2,1,0,0,0,0,0,0,6,0.00,0.00,'',58,1),(34,'S8A1',16,0,0,2,2,4,4,2,2,0,0,0,0,0,6,0.00,0.00,'',61,2),(35,'S8A2',8,0,0,0,2,2,2,2,0,0,0,0,0,0,6,0.00,0.00,'',63,1),(36,'S8A3',16,0,0,2,4,4,4,2,0,0,0,0,0,0,6,0.00,0.00,'',65,2),(37,'S8B1',16,0,2,2,4,4,2,2,0,0,0,0,0,0,6,0.00,0.00,'',67,2),(38,'S8B2',8,0,0,2,2,2,2,0,0,0,0,0,0,0,6,0.00,0.00,'',69,1),(39,'L4',312,0,0,0,78,78,78,78,0,0,0,0,0,0,7,0.00,0.00,'',38,78),(40,'P4',308,0,0,77,77,77,77,0,0,0,0,0,0,0,7,0.00,0.00,'',41,77),(41,'X36',18,0,0,18,0,0,0,0,0,0,0,0,0,0,7,0.00,0.00,'',43,2),(42,'X37',45,0,0,0,45,0,0,0,0,0,0,0,0,0,7,0.00,0.00,'',46,5),(43,'X38',63,0,0,0,0,63,0,0,0,0,0,0,0,0,7,0.00,0.00,'',50,7),(44,'X39',36,0,0,0,0,0,36,0,0,0,0,0,0,0,7,0.00,0.00,'',51,4),(45,'X40',18,0,0,0,0,0,0,18,0,0,0,0,0,0,7,0.00,0.00,'',53,2),(46,'S12A',864,0,0,72,144,216,216,144,72,0,0,0,0,0,8,9.90,8553.60,'',54,72),(47,'S12B',216,0,18,36,54,54,36,18,0,0,0,0,0,0,8,9.90,2138.40,'',56,18),(48,'S6A1',114,0,0,19,19,19,19,19,19,0,0,0,0,0,8,9.90,1128.60,'',57,19),(49,'S6A2',78,0,0,0,13,26,26,13,0,0,0,0,0,0,8,9.90,772.20,'',58,13),(50,'S6B1',24,0,4,4,4,4,4,4,0,0,0,0,0,0,8,9.90,237.60,'',59,4),(51,'S6B2',48,0,0,8,16,16,8,0,0,0,0,0,0,0,8,9.90,475.20,'',60,8),(52,'S8A1',392,0,0,49,49,98,98,49,49,0,0,0,0,0,8,9.90,3880.80,'',61,49),(53,'S8A2',56,0,0,0,14,14,14,14,0,0,0,0,0,0,8,9.90,554.40,'',63,7),(54,'S8A3',296,0,0,37,74,74,74,37,0,0,0,0,0,0,8,9.90,2930.40,'',65,37),(55,'S8B1',120,0,15,15,30,30,15,15,0,0,0,0,0,0,8,9.90,1188.00,'',67,15),(56,'S8B2',72,0,0,18,18,18,18,0,0,0,0,0,0,0,8,9.90,712.80,'',69,9),(57,'S12A',372,0,0,31,62,93,93,62,31,0,0,0,0,0,9,9.90,3682.80,'',54,31),(58,'S12B',60,0,5,10,15,15,10,5,0,0,0,0,0,0,9,9.90,594.00,'',56,5),(59,'S6A1',30,0,0,5,5,5,5,5,5,0,0,0,0,0,9,9.90,297.00,'',57,5),(60,'S6A2',24,0,0,0,4,8,8,4,0,0,0,0,0,0,9,9.90,237.60,'',58,4),(61,'S6B1',12,0,2,2,2,2,2,2,0,0,0,0,0,0,9,9.90,118.80,'',59,2),(62,'S6B2',12,0,0,2,4,4,2,0,0,0,0,0,0,0,9,9.90,118.80,'',60,2),(63,'S8A1',56,0,0,7,7,14,14,7,7,0,0,0,0,0,9,9.90,554.40,'',61,7),(64,'S8A2',16,0,0,0,4,4,4,4,0,0,0,0,0,0,9,9.90,158.40,'',63,2),(65,'S8A3',32,0,0,4,8,8,8,4,0,0,0,0,0,0,9,9.90,316.80,'',65,4),(66,'S8B1',32,0,4,4,8,8,4,4,0,0,0,0,0,0,9,9.90,316.80,'',67,4),(67,'S8B2',16,0,0,4,4,4,4,0,0,0,0,0,0,0,9,9.90,158.40,'',69,2),(68,'S12A',432,0,0,36,72,108,108,72,36,0,0,0,0,0,10,9.90,4276.80,'',54,36),(69,'S12B',108,0,9,18,27,27,18,9,0,0,0,0,0,0,10,9.90,1069.20,'',56,9),(70,'S6A1',60,0,0,10,10,10,10,10,10,0,0,0,0,0,10,9.90,594.00,'',57,10),(71,'S6A2',36,0,0,0,6,12,12,6,0,0,0,0,0,0,10,9.90,356.40,'',58,6),(72,'S6B1',12,0,2,2,2,2,2,2,0,0,0,0,0,0,10,9.90,118.80,'',59,2),(73,'S6B2',24,0,0,4,8,8,4,0,0,0,0,0,0,0,10,9.90,237.60,'',60,4),(74,'S8A1',296,0,0,37,37,74,74,37,37,0,0,0,0,0,10,9.90,2930.40,'',61,37),(75,'S8A2',32,0,0,0,8,8,8,8,0,0,0,0,0,0,10,9.90,316.80,'',63,4),(76,'S8A3',104,0,0,13,26,26,26,13,0,0,0,0,0,0,10,9.90,1029.60,'',65,13),(77,'S8B1',64,0,8,8,16,16,8,8,0,0,0,0,0,0,10,9.90,633.60,'',67,8),(78,'S8B2',32,0,0,8,8,8,8,0,0,0,0,0,0,0,10,9.90,316.80,'',69,4),(95,'40-45/123321',240,0,20,40,60,60,40,20,0,0,0,0,0,0,29,0.00,0.00,'',76,20),(96,'40-45/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,30,0.00,0.00,'',76,50),(97,'40-45/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,31,0.00,0.00,'',76,50),(98,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,32,0.00,0.00,'',75,50),(99,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,33,0.00,0.00,'',75,40),(100,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,34,0.00,0.00,'',75,30),(101,'36-41/123321',240,0,20,40,60,60,40,20,0,0,0,0,0,0,35,0.00,0.00,'',75,20),(102,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,36,0.00,0.00,'',75,50),(103,'36-41/123321',420,0,35,70,105,105,70,35,0,0,0,0,0,0,37,0.00,0.00,'',75,35),(104,'36-41/123321',420,0,35,70,105,105,70,35,0,0,0,0,0,0,38,0.00,0.00,'',75,35),(105,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,39,0.00,0.00,'',75,50),(106,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,40,0.00,0.00,'',75,50),(107,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,41,0.00,0.00,'',75,40),(108,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,42,0.00,0.00,'',75,40),(109,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,43,0.00,0.00,'',75,50),(110,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,44,0.00,0.00,'',75,30),(111,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,45,0.00,0.00,'',75,40),(112,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,46,0.00,0.00,'',75,50),(113,'36-41/123321',540,0,45,90,135,135,90,45,0,0,0,0,0,0,47,0.00,0.00,'',75,45),(114,'36-41/123321',540,0,45,90,135,135,90,45,0,0,0,0,0,0,48,0.00,0.00,'',75,45),(115,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,49,0.00,0.00,'',75,40),(116,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,50,0.00,0.00,'',75,30),(117,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,51,0.00,0.00,'',75,30),(118,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,52,0.00,0.00,'',75,40),(119,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,53,0.00,0.00,'',75,30),(120,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,54,0.00,0.00,'',75,30),(121,'36-41/123321',720,0,60,120,180,180,120,60,0,0,0,0,0,0,55,0.00,0.00,'',75,60),(122,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,56,0.00,0.00,'',75,50),(123,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,57,0.00,0.00,'',75,40),(124,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,58,0.00,0.00,'',75,50),(125,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,59,0.00,0.00,'',75,50),(126,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,60,0.00,0.00,'',75,40),(127,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,61,0.00,0.00,'',75,40),(128,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,62,0.00,0.00,'',75,30),(129,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,63,0.00,0.00,'',75,50),(130,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,64,0.00,0.00,'',75,50),(131,'36-41/123321',420,0,35,70,105,105,70,35,0,0,0,0,0,0,65,0.00,0.00,'',75,35),(132,'36-41/123321',420,0,35,70,105,105,70,35,0,0,0,0,0,0,66,0.00,0.00,'',75,35),(133,'36-41/123321',720,0,60,120,180,180,120,60,0,0,0,0,0,0,67,0.00,0.00,'',75,60),(134,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,68,0.00,0.00,'',75,30),(135,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,69,0.00,0.00,'',75,50),(136,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,70,0.00,0.00,'',75,50),(137,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,71,0.00,0.00,'',75,30),(138,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,72,0.00,0.00,'',75,40),(139,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,73,0.00,0.00,'',75,40),(140,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,74,0.00,0.00,'',75,30),(141,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,75,0.00,0.00,'',75,30),(142,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,76,0.00,0.00,'',75,50),(143,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,77,0.00,0.00,'',75,30),(144,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,78,0.00,0.00,'',75,40),(145,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,79,0.00,0.00,'',75,30),(146,'36-41/123321',420,0,35,70,105,105,70,35,0,0,0,0,0,0,80,0.00,0.00,'',75,35),(147,'36-41/123321',420,0,35,70,105,105,70,35,0,0,0,0,0,0,81,0.00,0.00,'',75,35),(148,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,82,0.00,0.00,'',75,50),(149,'36-41/123321',240,0,20,40,60,60,40,20,0,0,0,0,0,0,83,0.00,0.00,'',75,20),(150,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,84,0.00,0.00,'',75,30),(151,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,85,0.00,0.00,'',75,50),(152,'36-41/123321',240,0,20,40,60,60,40,20,0,0,0,0,0,0,86,0.00,0.00,'',75,20),(153,'36-41/123321',360,0,30,60,90,90,60,30,0,0,0,0,0,0,87,0.00,0.00,'',75,30),(154,'36-41/123321',720,0,60,120,180,180,120,60,0,0,0,0,0,0,88,0.00,0.00,'',75,60),(155,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,89,0.00,0.00,'',75,50),(156,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,90,0.00,0.00,'',75,50),(157,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,91,0.00,0.00,'',75,50),(158,'36-41/123321',720,0,60,120,180,180,120,60,0,0,0,0,0,0,92,0.00,0.00,'',75,60),(159,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,93,0.00,0.00,'',75,50),(160,'36-41/123321',720,0,60,120,180,180,120,60,0,0,0,0,0,0,94,0.00,0.00,'',75,60),(161,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,95,0.00,0.00,'',75,50),(162,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,96,0.00,0.00,'',75,50),(163,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,97,0.00,0.00,'',75,50),(164,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,98,0.00,0.00,'',75,50),(165,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,99,0.00,0.00,'',75,40),(166,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,100,0.00,0.00,'',75,50),(167,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,101,0.00,0.00,'',75,50),(168,'36-41/123321',720,0,60,120,180,180,120,60,0,0,0,0,0,0,102,0.00,0.00,'',75,60),(169,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,103,0.00,0.00,'',75,40),(170,'36-41/123321',720,0,60,120,180,180,120,60,0,0,0,0,0,0,104,0.00,0.00,'',75,60),(171,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,105,0.00,0.00,'',75,40),(172,'36-41/123321',720,0,60,120,180,180,120,60,0,0,0,0,0,0,106,0.00,0.00,'',75,60),(173,'36-41/123321',480,0,40,80,120,120,80,40,0,0,0,0,0,0,107,0.00,0.00,'',75,40),(174,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,108,0.00,0.00,'',75,50),(175,'36-41/123321',600,0,50,100,150,150,100,50,0,0,0,0,0,0,109,0.00,0.00,'',75,50),(179,'36-41/112211',120,0,15,15,30,30,15,15,0,0,0,0,0,0,113,0.00,0.00,'',77,15),(180,'36-41/112211',120,0,15,15,30,30,15,15,0,0,0,0,0,0,114,0.00,0.00,'',77,15),(181,'36-41/112211',200,0,25,25,50,50,25,25,0,0,0,0,0,0,115,0.00,0.00,'',77,25),(182,'36-41/112211',160,0,20,20,40,40,20,20,0,0,0,0,0,0,116,0.00,0.00,'',77,20),(183,'36-41/112211',160,0,20,20,40,40,20,20,0,0,0,0,0,0,117,0.00,0.00,'',77,20),(184,'36-41/112211',120,0,15,15,30,30,15,15,0,0,0,0,0,0,118,0.00,0.00,'',77,15),(185,'36-41/112211',120,0,15,15,30,30,15,15,0,0,0,0,0,0,119,0.00,0.00,'',78,15),(186,'36-41/112211',160,0,20,20,40,40,20,20,0,0,0,0,0,0,120,0.00,0.00,'',77,20),(187,'36-41/112211',272,0,34,34,68,68,34,34,0,0,0,0,0,0,121,0.00,0.00,'',77,34),(188,'36-41/112211',240,0,30,30,60,60,30,30,0,0,0,0,0,0,122,0.00,0.00,'',77,30),(189,'36-41/112211',120,0,15,15,30,30,15,15,0,0,0,0,0,0,123,0.00,0.00,'',77,15),(190,'36-41/112211',160,0,20,20,40,40,20,20,0,0,0,0,0,0,124,0.00,0.00,'',77,20),(191,'36-41/112211',120,0,15,15,30,30,15,15,0,0,0,0,0,0,125,0.00,0.00,'',77,15),(192,'36-41/112211',160,0,20,20,40,40,20,20,0,0,0,0,0,0,126,0.00,0.00,'',77,20),(193,'36-41/112211',160,0,20,20,40,40,20,20,0,0,0,0,0,0,127,0.00,0.00,'',77,20),(194,'36-41/112211',320,0,40,40,80,80,40,40,0,0,0,0,0,0,128,0.00,0.00,'',77,40),(195,'36-41/112211',240,0,30,30,60,60,30,30,0,0,0,0,0,0,129,0.00,0.00,'',77,30),(196,'36-41/112211',120,0,15,15,30,30,15,15,0,0,0,0,0,0,130,0.00,0.00,'',77,15),(197,'36-41/112211',160,0,20,20,40,40,20,20,0,0,0,0,0,0,131,0.00,0.00,'',77,20),(198,'装箱方法待确认男鞋',80,0,6,11,23,23,11,6,0,0,0,0,0,0,132,0.00,0.00,'',80,1),(199,'装箱方法待确认2',120,0,20,20,20,20,20,20,0,0,0,0,0,0,132,0.00,0.00,'',81,1);
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=66 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_production_info`
--

LOCK TABLES `order_shoe_production_info` WRITE;
/*!40000 ALTER TABLE `order_shoe_production_info` DISABLE KEYS */;
INSERT INTO `order_shoe_production_info` VALUES (14,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,14),(15,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,15),(16,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,16),(17,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,17),(18,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,18),(19,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,19),(20,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,20),(21,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,21),(22,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,22),(23,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,23),(24,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,24),(25,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,25),(26,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,26),(27,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,27),(28,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,28),(29,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,29),(30,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,30),(31,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,31),(32,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,32),(33,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,33),(34,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,34),(35,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,35),(36,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,36),(37,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,37),(38,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,38),(39,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,39),(40,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,40),(41,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,41),(42,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,42),(43,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,43),(44,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,44),(45,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,45),(46,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,46),(47,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,47),(48,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,48),(49,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,49),(50,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,50),(51,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,51),(52,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,52),(53,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,53),(54,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,54),(55,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,55),(56,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,56),(57,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,57),(58,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,58),(59,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,59),(60,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,60),(61,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,61),(62,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,62),(63,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,63),(64,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,64),(65,NULL,NULL,NULL,NULL,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,65);
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
) ENGINE=InnoDB AUTO_INCREMENT=74 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_status`
--

LOCK TABLES `order_shoe_status` WRITE;
/*!40000 ALTER TABLE `order_shoe_status` DISABLE KEYS */;
INSERT INTO `order_shoe_status` VALUES (22,14,0,0),(23,15,0,0),(24,16,0,0),(25,17,0,0),(26,18,0,0),(27,19,0,0),(28,20,0,0),(29,21,0,0),(30,22,0,0),(31,23,0,0),(32,24,0,0),(33,25,0,0),(34,26,0,0),(35,27,0,0),(36,28,0,0),(37,29,0,0),(38,30,0,0),(39,31,0,0),(40,32,0,0),(41,33,0,0),(42,34,0,0),(43,35,0,0),(44,36,0,0),(45,37,0,0),(46,38,0,0),(47,39,0,0),(48,40,0,0),(49,41,0,0),(50,42,0,0),(51,43,0,0),(52,44,0,0),(53,45,0,0),(54,46,0,0),(55,47,0,0),(56,48,0,0),(57,49,0,0),(58,50,0,0),(59,51,0,0),(60,52,0,0),(61,53,0,0),(62,54,0,0),(63,55,0,0),(64,56,0,0),(65,57,0,0),(66,58,0,0),(67,59,0,0),(68,60,0,0),(69,61,0,0),(70,62,0,0),(71,63,0,0),(72,64,0,0),(73,65,0,0);
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
INSERT INTO `order_shoe_status_reference` VALUES (0,'投产指令单创建'),(1,'投产指令单下发'),(2,'一次BOM填写'),(3,'一次BOM下发'),(4,'面料单位用量计算'),(5,'面料单位用量下发'),(6,'一次采购订单创建'),(7,'一次采购订单下发'),(8,'一次采购入库'),(9,'技术部调版分配'),(10,'技术部调版下发'),(11,'二次BOM填写'),(12,'二次BOM下发'),(13,'二次BOM用量审核'),(14,'二次BOM用量审核下发'),(15,'二次采购入库'),(16,'材料到齐通知'),(17,'生产排期，分配'),(18,'生产开始'),(19,'裁断材料出库'),(20,'裁断，批皮工价填报'),(21,'财务部审核'),(22,'生产副总审核'),(23,'裁断开始'),(24,'裁断结束'),(25,'半成品中转入库'),(26,'半成品中转针车材料出库'),(27,'针车及预备工序填报'),(28,'财务部审核'),(29,'生产副总审核'),(30,'针车预备开始'),(31,'针车预备结束'),(32,'针车开始'),(33,'针车结束'),(34,'鞋包中转仓入库'),(35,'鞋包中转仓出库'),(36,'成型材料出库'),(37,'成型工价填报'),(38,'财务部审核'),(39,'生产副总审核'),(40,'成型开始'),(41,'成型结束'),(42,'生产结束');
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
  `unit_price` decimal(10,2) DEFAULT '0.00',
  `currency_type` char(4) DEFAULT '',
  `total_amount` int DEFAULT '0',
  `customer_color_name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`order_shoe_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=133 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_shoe_type`
--

LOCK TABLES `order_shoe_type` WRITE;
/*!40000 ALTER TABLE `order_shoe_type` DISABLE KEYS */;
INSERT INTO `order_shoe_type` VALUES (29,171,19,0,0,0,0,62.00,'RMB',0,'MARINO'),(30,172,19,0,0,0,0,62.00,'RMB',0,'CUERO'),(31,173,19,0,0,0,0,62.00,'RMB',0,'MARRON'),(32,174,20,0,0,0,0,60.00,'RMB',0,'NEGRO'),(33,175,20,0,0,0,0,60.00,'RMB',0,'CUERO'),(34,176,21,0,0,0,0,53.00,'RMB',0,'CUERO'),(35,177,21,0,0,0,0,53.00,'RMB',0,'BURDEOS'),(36,158,22,0,0,0,0,0.00,'',0,'BLACK'),(37,178,23,0,0,0,0,0.00,'',0,'BLACK'),(38,179,23,0,0,0,0,0.00,'',0,'CAMEL'),(39,156,24,0,0,0,0,58.50,'RMB',0,'BLACK'),(40,157,24,0,0,0,0,58.50,'RMB',0,'CAMEL'),(41,187,25,0,0,0,0,0.00,'',0,'BLACK'),(42,188,25,0,0,0,0,0.00,'',0,'BEIGE'),(43,168,26,0,0,0,0,0.00,'',0,'BLACK'),(44,169,26,0,0,0,0,0.00,'',0,'CAMEL'),(45,186,26,0,0,0,0,0.00,'',0,'TAUPE'),(46,192,27,0,0,0,0,0.00,'',0,'BLACK'),(47,193,27,0,0,0,0,0.00,'',0,'TAUPE'),(48,194,27,0,0,0,0,0.00,'',0,'BEIGE'),(49,180,28,0,0,0,0,0.00,'',0,'BLACK'),(50,181,28,0,0,0,0,0.00,'',0,'BEIGE'),(51,182,28,0,0,0,0,0.00,'',0,'CAMEL'),(52,164,29,0,0,0,0,0.00,'',0,'BLACK'),(53,165,29,0,0,0,0,0.00,'',0,'BEIGE'),(54,166,29,0,0,0,0,0.00,'',0,'CAMEL'),(55,183,30,0,0,0,0,0.00,'',0,'BLACK'),(56,184,30,0,0,0,0,0.00,'',0,'BEIGE'),(57,185,30,0,0,0,0,0.00,'',0,'CAMEL'),(58,189,31,0,0,0,0,0.00,'',0,'BLACK'),(59,190,31,0,0,0,0,0.00,'',0,'CAMEL'),(60,191,31,0,0,0,0,0.00,'',0,'BEIGE'),(61,197,32,0,0,0,0,0.00,'',0,'BLACK'),(62,198,32,0,0,0,0,0.00,'',0,'TAUPE'),(63,195,33,0,0,0,0,60.50,'RMB',0,'BLACK'),(64,196,33,0,0,0,0,60.50,'RMB',0,'BROWN'),(65,202,34,0,0,0,0,0.00,'',0,'CAMEL'),(66,203,34,0,0,0,0,0.00,'',0,'TAUPE'),(67,199,35,0,0,0,0,62.50,'RMB',0,'BLACK'),(68,200,35,0,0,0,0,62.50,'RMB',0,'BROWN'),(69,201,35,0,0,0,0,62.50,'RMB',0,'CAMEL'),(70,204,36,0,0,0,0,61.50,'RMB',0,'BLACK'),(71,205,36,0,0,0,0,61.50,'RMB',0,'CAMEL'),(72,206,36,0,0,0,0,61.50,'RMB',0,'BROWN'),(73,207,37,0,0,0,0,76.50,'RMB',0,'BLACK'),(74,208,37,0,0,0,0,76.50,'RMB',0,'BROWN'),(75,209,37,0,0,0,0,76.50,'RMB',0,'CAMEL'),(76,210,38,0,0,0,0,58.00,'RMB',0,'BLACK'),(77,211,38,0,0,0,0,58.00,'RMB',0,'CAMEL'),(78,212,38,0,0,0,0,58.00,'RMB',0,'BROWN'),(79,213,39,0,0,0,0,72.50,'RMB',0,'BLACK'),(80,214,39,0,0,0,0,72.50,'RMB',0,'CAMEL'),(81,215,39,0,0,0,0,72.50,'RMB',0,'TAUPE'),(82,219,40,0,0,0,0,73.50,'RMB',0,'BLACK'),(83,220,40,0,0,0,0,73.50,'RMB',0,'CAMEL'),(84,221,40,0,0,0,0,73.50,'RMB',0,'BROWN'),(85,222,41,0,0,0,0,59.50,'RMB',0,'BLACK'),(86,223,41,0,0,0,0,59.50,'RMB',0,'CAMEL'),(87,224,41,0,0,0,0,59.50,'RMB',0,'BROWN'),(88,225,42,0,0,0,0,0.00,'',0,'BLACK'),(89,226,42,0,0,0,0,0.00,'',0,'BROWN'),(90,227,42,0,0,0,0,0.00,'',0,'BEIGE'),(91,228,43,0,0,0,0,0.00,'',0,'BLACK'),(92,229,43,0,0,0,0,0.00,'',0,'CAMEL'),(93,230,43,0,0,0,0,0.00,'',0,'BEIGE'),(94,231,44,0,0,0,0,0.00,'',0,'BLACK'),(95,232,44,0,0,0,0,0.00,'',0,'CAMEL'),(96,233,44,0,0,0,0,0.00,'',0,'BEIGE'),(97,234,45,0,0,0,0,0.00,'',0,'BLACK'),(98,235,45,0,0,0,0,0.00,'',0,'CAMEL'),(99,236,45,0,0,0,0,0.00,'',0,'BEIGE '),(100,237,46,0,0,0,0,0.00,'',0,'BLACK'),(101,238,46,0,0,0,0,0.00,'',0,'TAUPE'),(102,239,47,0,0,0,0,0.00,'',0,'BLACK'),(103,240,47,0,0,0,0,0.00,'',0,'CAMEL'),(104,241,48,0,0,0,0,0.00,'',0,'BLACK'),(105,242,48,0,0,0,0,0.00,'',0,'CAMEL'),(106,243,49,0,0,0,0,0.00,'',0,'BLACK'),(107,244,49,0,0,0,0,0.00,'',0,'CAMEL'),(108,245,50,0,0,0,0,0.00,'',0,'BLACK'),(109,246,50,0,0,0,0,0.00,'',0,'TAUPE '),(113,247,53,0,0,0,0,10.20,'USD',0,'BLACK'),(114,248,53,0,0,0,0,10.20,'USD',0,'TAUPE'),(115,133,54,0,0,0,0,10.00,'USD',0,'TAUPE'),(116,249,55,0,0,0,0,12.00,'USD',0,'TAUPE'),(117,250,56,0,0,0,0,10.00,'USD',0,'BLACK'),(118,251,56,0,0,0,0,10.00,'USD',0,'TAUPE'),(119,252,57,0,0,0,0,11.50,'USD',0,'BLACK'),(120,254,58,0,0,0,0,10.40,'USD',0,'CAMEL'),(121,123,59,0,0,0,0,10.00,'USD',0,'BLACK'),(122,124,59,0,0,0,0,10.00,'USD',0,'TAUPE'),(123,129,60,0,0,0,0,10.00,'USD',0,'BLACK'),(124,140,61,0,0,0,0,9.70,'USD',0,'TAUPE'),(125,141,61,0,0,0,0,9.70,'USD',0,'CAMEL'),(126,142,61,0,0,0,0,9.70,'USD',0,'BLACK'),(127,260,62,0,0,0,0,10.00,'USD',0,'BLACK'),(128,255,63,0,0,0,0,12.50,'USD',0,'BLACK'),(129,258,63,0,0,0,0,12.50,'USD',0,'TAUPE'),(130,126,64,0,0,0,0,9.40,'USD',0,'BLACK'),(131,127,64,0,0,0,0,9.40,'USD',0,'TAUPE'),(132,38,65,0,0,0,0,0.00,'',0,'BROWN');
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
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_status`
--

LOCK TABLES `order_status` WRITE;
/*!40000 ALTER TABLE `order_status` DISABLE KEYS */;
INSERT INTO `order_status` VALUES (15,6,0,19),(16,6,0,20),(17,6,0,21),(18,6,0,22),(19,6,1,23),(20,7,0,24),(21,7,0,25),(22,7,0,26),(23,6,0,27),(24,6,0,28),(25,7,0,29),(26,6,0,30),(27,6,0,31),(28,6,0,32),(29,6,0,33),(30,6,0,34),(31,6,0,35),(32,6,0,36),(33,6,0,37),(34,7,0,38),(35,6,0,39),(36,7,0,40),(37,7,0,41),(38,7,0,42),(39,7,0,43),(40,7,0,44),(41,7,0,45),(42,7,0,46),(43,6,0,47),(44,6,0,48),(45,6,0,49),(46,6,0,50),(47,6,0,51),(48,6,0,52),(49,6,0,53),(50,6,0,54),(51,6,0,55),(52,6,1,56),(53,6,1,57),(54,6,1,58),(55,6,1,59),(56,6,1,60),(57,6,1,61),(58,6,1,62),(59,6,1,63),(60,6,1,64),(61,6,1,65),(62,6,1,66),(63,6,1,67),(64,6,1,68),(65,7,0,69),(66,6,0,70);
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
  `outbound_type` tinyint NOT NULL DEFAULT (_utf8mb4'0') COMMENT '0：自产\n1：废料\n2：外包\n3：复合',
  `outbound_department` tinyint DEFAULT NULL COMMENT '0: cutting, 1: sewing, 2: molding',
  `picker` varchar(15) DEFAULT NULL,
  `outbound_address` varchar(100) DEFAULT NULL,
  `material_storage_id` bigint DEFAULT NULL,
  `size_material_storage_id` bigint DEFAULT NULL,
  `outsource_info_id` int DEFAULT NULL,
  PRIMARY KEY (`outbound_record_id`),
  KEY `fk_outstock_record` (`material_storage_id`),
  KEY `fk_outstock_record0` (`size_material_storage_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `item_cost` decimal(10,2) DEFAULT '0.00',
  `item_total_cost` decimal(10,2) DEFAULT (_utf8mb4'0'),
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
  `factory_id` int NOT NULL AUTO_INCREMENT,
  `factory_name` varchar(50) DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL DEFAULT (_utf8mb4'0'),
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
  `outsource_info_id` int unsigned NOT NULL AUTO_INCREMENT,
  `outsource_type` varchar(20) NOT NULL COMMENT '0=裁断\n1=针车\n2=成型',
  `factory_name` varchar(50) NOT NULL,
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
  KEY `fk_outsource_info_outsource_factory` (`factory_name`)
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
  `packaging_info_name` varchar(15) NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `packaging_info`
--

LOCK TABLES `packaging_info` WRITE;
/*!40000 ALTER TABLE `packaging_info` DISABLE KEYS */;
INSERT INTO `packaging_info` VALUES (34,6,'7.5单码','US男',16,0,12,0,0,0,0,0,0,0,0,0,0,0,12),(35,6,'8单码','US男',16,0,0,12,0,0,0,0,0,0,0,0,0,0,12),(36,6,'8.5单码','US男',16,0,0,0,12,0,0,0,0,0,0,0,0,0,12),(37,6,'9单码','US男',16,0,0,0,0,12,0,0,0,0,0,0,0,0,12),(38,7,'L4','EU',15,0,0,0,1,1,1,1,0,0,0,0,0,0,4),(39,6,'9.5单码','US男',16,0,0,0,0,0,12,0,0,0,0,0,0,0,12),(40,6,'10单码','US男',16,0,0,0,0,0,0,12,0,0,0,0,0,0,12),(41,7,'P4','EU',15,0,0,1,1,1,1,0,0,0,0,0,0,0,4),(42,6,'10.5单码','US男',16,0,0,0,0,0,0,0,12,0,0,0,0,0,12),(43,7,'X36','EU',15,0,0,9,0,0,0,0,0,0,0,0,0,0,9),(44,6,'11单码','US男',16,0,0,0,0,0,0,0,0,12,0,0,0,0,12),(46,7,'X37','EU',15,0,0,0,9,0,0,0,0,0,0,0,0,0,9),(50,7,'X38','EU',15,0,0,0,0,9,0,0,0,0,0,0,0,0,9),(51,7,'X39','EU',15,0,0,0,0,0,9,0,0,0,0,0,0,0,9),(52,6,'12单码','US男',16,0,0,0,0,0,0,0,0,0,0,12,0,0,12),(53,7,'X40','EU',15,0,0,0,0,0,0,9,0,0,0,0,0,0,9),(54,9,'S12A','EU',15,0,0,1,2,3,3,2,1,0,0,0,0,0,12),(55,6,'13单码','US男',16,0,0,0,0,0,0,0,0,0,0,0,0,12,12),(56,9,'S12B','EU',15,0,1,2,3,3,2,1,0,0,0,0,0,0,12),(57,9,'S6A1','EU',15,0,0,1,1,1,1,1,1,0,0,0,0,0,6),(58,9,'S6A2','EU',15,0,0,0,1,2,2,1,0,0,0,0,0,0,6),(59,9,'S6B1','EU',15,0,1,1,1,1,1,1,0,0,0,0,0,0,6),(60,9,'S6B2','EU',15,0,0,1,2,2,1,0,0,0,0,0,0,0,6),(61,9,'S8A1','EU',15,0,0,1,1,2,2,1,1,0,0,0,0,0,8),(63,9,'S8A2','EU',15,0,0,0,2,2,2,2,0,0,0,0,0,0,8),(64,6,'7单码','US男',16,12,0,0,0,0,0,0,0,0,0,0,0,0,12),(65,9,'S8A3','EU',15,0,0,1,2,2,2,1,0,0,0,0,0,0,8),(66,10,'C12A','EU',15,0,0,0,0,0,0,1,2,3,3,2,1,0,12),(67,9,'S8B1','EU',15,0,1,1,2,2,1,1,0,0,0,0,0,0,8),(69,9,'S8B2','EU',15,0,0,2,2,2,2,0,0,0,0,0,0,0,8),(70,6,'S12A','EU男',24,1,2,3,3,2,1,0,0,0,0,0,0,0,12),(75,11,'36-41/123321','EU女',22,0,1,2,3,3,2,1,0,0,0,0,0,0,12),(76,11,'40-45/123321','EU男',21,0,1,2,3,3,2,1,0,0,0,0,0,0,12),(77,9,'36-41/112211','EU女',22,0,1,1,2,2,1,1,0,0,0,0,0,0,8),(78,10,'36-41/112211','EU女',22,0,1,1,2,2,1,1,0,0,0,0,0,0,8),(80,10,'装箱方法待确认','EU男',21,0,6,11,23,23,11,6,0,0,0,0,0,0,80),(81,10,'装箱方法待确认','EU男',21,0,20,20,20,20,20,20,0,0,0,0,0,0,120);
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
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='裁断，针车，成型工序名字一览';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `procedure_reference`
--

LOCK TABLES `procedure_reference` WRITE;
/*!40000 ALTER TABLE `procedure_reference` DISABLE KEYS */;
INSERT INTO `procedure_reference` VALUES (4,'后跟合缝','针车预备',0.1),(6,'预备2','针车预备',12),(7,'预备3','针车预备',5),(8,'单针车内外边排','针车',0.36),(9,'车鞋眼片滴塑标4个','针车',0.5),(10,'反车后排里布放保险丝','针车',0.5),(11,'成型1','成型',1),(12,'成型2','成型',2),(13,'成型3','成型',3),(14,'单针车鞋眼片','针车',0.6),(16,'高靴','裁断',0.58),(17,'矮靴','裁断',0.47),(18,'切割-10片','裁断',0.15);
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
  `burn_sole_craft` varchar(100) DEFAULT NULL,
  `craft_remark` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`production_instruction_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;
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
  `pre_craft_name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`production_instruction_item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=413 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `order_shoe_id` bigint DEFAULT NULL,
  `purchase_order_status` char(1) DEFAULT NULL,
  PRIMARY KEY (`purchase_order_id`),
  UNIQUE KEY `purchase_order_rid_UNIQUE` (`purchase_order_rid`),
  KEY `fk_purchase_orders_boms` (`bom_id`),
  KEY `fk_purchase_order_order` (`order_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `semifinished_estimated_amount` int DEFAULT '0',
  `semifinished_actual_amount` int DEFAULT '0',
  `semifinished_amount` int NOT NULL DEFAULT '0',
  `semifinished_status` tinyint DEFAULT NULL COMMENT '0：未入库\n1：已入库\n2：已出库',
  `semifinished_object` tinyint DEFAULT NULL COMMENT '0: 半成品\n1: 鞋包',
  PRIMARY KEY (`semifinished_shoe_id`),
  UNIQUE KEY `unq_semifinished_shoe_storage` (`order_shoe_type_id`,`semifinished_object`),
  KEY `fk_semifinished_shoe_storage` (`order_shoe_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `shoe_department_id` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`shoe_id`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shoe`
--

LOCK TABLES `shoe` WRITE;
/*!40000 ALTER TABLE `shoe` DISABLE KEYS */;
INSERT INTO `shoe` VALUES (1,'1001','wang','shejiyibu'),(2,'C230571','','开发二部'),(3,'3E1122','邱真汗','开发一部'),(4,'C8803M1','','开发二部'),(5,'3E3027','','开发一部'),(6,'JC3670-3A33','郑建超','开发三部'),(7,'3E25635','','开发一部'),(8,'3F3776','','开发一部'),(9,'3F5015','','开发一部'),(10,'JC25539-C288','','开发三部'),(11,'3F6602','','开发一部'),(12,'3F3585','','开发一部'),(13,'3F5958','','开发一部'),(14,'3F6302','','开发一部'),(15,'3G5966','','开发一部'),(16,'D231191','','开发二部'),(17,'3G5186','','开发一部'),(18,'D81C021','','开发二部'),(19,'C80092H3','','开发二部'),(20,'JC6359-C351','','开发三部'),(21,'JC6359-C352','','开发三部'),(22,'JC6359-C353','','开发三部'),(23,'3F3589','','开发一部'),(24,'3F3583A','','开发一部'),(25,'0E19571','','开发一部'),(26,'0E19526','','开发一部'),(27,'3E3077','','开发一部'),(28,'3E30723','','开发一部'),(29,'3E30725','','开发一部'),(30,'JC80120-E80','','开发三部'),(31,'JC80120-E181','','开发三部'),(32,'3E5711','','开发一部'),(33,'2E00719','','开发一部'),(34,'3E23526','','开发一部'),(35,'D2500710','','开发二部'),(36,'D2109610','','开发二部'),(37,'C100928','','开发二部'),(38,'5F3571','','开发一部'),(39,'5G5131A','','开发一部'),(40,'2G56016','','开发一部'),(41,'2G56017','','开发一部'),(42,'2G50225','','开发一部'),(43,'2F33112','','开发一部'),(44,'2G50227-P','','开发一部'),(45,'2G50225-P','','开发一部'),(46,'2F31319','','开发一部'),(47,'3E2566','','开发一部'),(48,'2F33116','','开发一部'),(49,'0E19533','','开发一部'),(50,'0E19532','','开发一部'),(51,'0E08116','','开发一部'),(52,'0E19550','','开发一部'),(53,'0E19539','','开发一部'),(54,'2E0079','','开发一部'),(55,'C10031','','开发二部'),(56,'3E29511','','开发一部'),(57,'C60986','','开发二部'),(58,'3E3061','','开发一部'),(59,'3F5098','','开发一部'),(60,'3E12212','','开发一部'),(61,'JC3926Y-C357X','','开发三部'),(62,'JC3926Y-C357','','开发三部'),(63,'JC9263-E206','','开发三部'),(64,'JC9263-E187','','开发三部'),(65,'JC2088-E205  电镀片','','开发三部'),(66,'5E0191','','开发一部'),(67,'JC8307-C398','','开发三部'),(68,'JC8307-E161','','开发三部'),(69,'JC2088-E161Z','','开发三部'),(70,'3E12213','','开发一部'),(71,'JC2088-E61','','开发三部'),(72,'5E0211','','开发一部'),(73,'JC8307-E208F','','开发三部'),(74,'3E5161','','开发一部'),(75,'5E0212','','开发一部'),(76,'3E5166','','开发一部'),(77,'3E30013','','开发一部'),(78,'3E30015','','开发一部'),(79,'0E7315','','开发一部'),(80,'0E17855','','开发一部'),(81,'5E0251','','开发一部'),(82,'5E0252','','开发一部'),(83,'5E3671','','开发一部'),(84,'5E3672','','开发一部'),(85,'3E3318','','开发一部'),(86,'3E3317','','开发一部'),(87,'5E0261','','开发一部'),(88,'5E0263','','开发一部'),(89,'5E0196','','开发一部'),(90,'2E01017','','开发一部'),(91,'0E19556','','开发一部'),(92,'2E3776','','开发一部'),(93,'3E2565','','开发一部'),(94,'0E21923','','开发一部'),(95,'0E21936','','开发一部'),(96,'0E21928','','开发一部');
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=261 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shoe_type`
--

LOCK TABLES `shoe_type` WRITE;
/*!40000 ALTER TABLE `shoe_type` DISABLE KEYS */;
INSERT INTO `shoe_type` VALUES (2,'shoe/1001/灰色/shoe_image.jpg',2,1),(3,'shoe/C230571/棕色/shoe_image.jpg',3,2),(4,'shoe/3E1122/黑色/shoe_image.jpg',1,3),(5,'shoe/C230571/深蓝/shoe_image.jpg',4,2),(6,'shoe/C8803M1/灰色/shoe_image.jpg',2,4),(7,NULL,1,4),(8,'shoe/3E3027/黑色/shoe_image.jpg',1,5),(9,'shoe/JC3670-3A33/米色/shoe_image.jpg',6,6),(10,'shoe/JC3670-3A33/牛仔蓝/shoe_image.jpg',7,6),(11,NULL,9,6),(12,NULL,1,7),(13,NULL,3,7),(14,'shoe/3E25635/驼色/shoe_image.jpg',10,7),(15,NULL,10,8),(16,'shoe/3F3776/黑色/shoe_image.jpg',1,8),(17,NULL,3,8),(18,'shoe/3F5015/黑色/shoe_image.jpg',1,9),(19,NULL,6,9),(20,NULL,10,9),(21,'shoe/JC25539-C288/黑色/shoe_image.jpg',5,10),(23,NULL,3,11),(24,'shoe/3F6602/枪色/shoe_image.jpg',11,11),(25,NULL,3,12),(26,NULL,5,12),(27,'shoe/3F3585/驼色/shoe_image.jpg',10,12),(28,'shoe/3F5958/棕色/shoe_image.jpg',3,13),(29,NULL,5,13),(30,'shoe/3F6302/米色/shoe_image.jpg',6,14),(31,NULL,5,14),(32,NULL,4,15),(33,'shoe/3G5966/棕色/shoe_image.jpg',3,15),(34,NULL,10,15),(35,NULL,3,16),(36,'shoe/D231191/深蓝/shoe_image.jpg',4,16),(37,NULL,10,16),(38,NULL,3,17),(39,NULL,4,17),(40,'shoe/3G5186/驼色/shoe_image.jpg',10,17),(41,NULL,4,18),(42,'shoe/D81C021/褐色/shoe_image.jpg',9,18),(43,NULL,10,18),(44,'shoe/C80092H3/棕色/shoe_image.jpg',3,19),(45,NULL,4,19),(46,NULL,10,19),(47,'shoe/JC6359-C351/黑色/shoe_image.jpg',5,20),(48,'shoe/JC6359-C352/黑色/shoe_image.jpg',5,21),(49,'shoe/JC6359-C353/黑色/shoe_image.jpg',5,22),(50,NULL,5,23),(51,'shoe/3F3589/米色/shoe_image.jpg',6,23),(52,NULL,10,23),(53,NULL,12,23),(54,'shoe/3F3583A/黑色/shoe_image.jpg',5,24),(55,NULL,9,24),(56,NULL,12,24),(57,'shoe/0E19571/黑色/shoe_image.jpg',5,25),(58,NULL,9,25),(59,NULL,5,26),(60,'shoe/0E19526/褐色/shoe_image.jpg',9,26),(61,NULL,5,27),(62,'shoe/3E3077/米色/shoe_image.jpg',6,27),(63,NULL,9,27),(64,NULL,5,28),(65,NULL,6,28),(66,'shoe/3E30723/褐色/shoe_image.jpg',9,28),(67,NULL,5,29),(68,'shoe/3E30725/米色/shoe_image.jpg',6,29),(69,NULL,9,29),(70,'shoe/JC80120-E80/黑色/shoe_image.jpg',5,30),(71,'shoe/JC80120-E181/黑色/shoe_image.jpg',5,31),(72,'shoe/3E5711/黑色/shoe_image.jpg',5,32),(73,NULL,9,32),(74,NULL,5,33),(75,'shoe/2E00719/米色/shoe_image.jpg',6,33),(76,NULL,9,33),(77,NULL,12,33),(78,NULL,5,34),(79,NULL,6,34),(80,'shoe/3E23526/褐色/shoe_image.jpg',9,34),(81,NULL,4,35),(82,NULL,5,35),(83,NULL,12,35),(84,'shoe/D2500710/褐色/shoe_image.jpg',9,35),(85,NULL,5,36),(86,NULL,12,36),(87,'shoe/D2109610/驼色/shoe_image.jpg',10,36),(90,'shoe/C100928/深蓝/shoe_image.jpg',4,37),(91,NULL,9,37),(92,NULL,12,37),(93,NULL,5,38),(94,'shoe/5F3571/褐色/shoe_image.jpg',9,38),(95,NULL,4,39),(96,'shoe/5G5131A/棕色/shoe_image.jpg',3,39),(97,NULL,12,39),(98,'shoe/2G56016/驼色/shoe_image.jpg',10,40),(99,NULL,1,41),(100,'shoe/2G56017/棕色/shoe_image.jpg',3,41),(101,NULL,10,41),(102,NULL,3,42),(103,'shoe/2G50225/驼色/shoe_image.jpg',10,42),(104,NULL,5,43),(105,NULL,6,43),(106,'shoe/2F33112/驼色/shoe_image.jpg',10,43),(107,'shoe/2G50227-P/棕色/shoe_image.jpg',3,44),(108,NULL,4,44),(109,NULL,10,44),(110,NULL,3,45),(111,'shoe/2G50225-P/驼色/shoe_image.jpg',10,45),(112,'shoe/2F31319/黑色/shoe_image.jpg',5,46),(113,NULL,6,46),(114,NULL,9,46),(115,NULL,13,46),(116,NULL,5,47),(117,'shoe/3E2566/驼色/shoe_image.jpg',10,47),(118,NULL,3,47),(119,NULL,1,48),(120,NULL,6,48),(121,NULL,11,48),(122,'shoe/2F33116/古铜/shoe_image.jpg',14,48),(123,'shoe/0E19533/黑色/shoe_image.jpg',1,49),(124,NULL,9,49),(125,NULL,10,49),(126,NULL,1,50),(127,NULL,9,50),(128,'shoe/0E19532/驼色/shoe_image.jpg',10,50),(129,NULL,5,51),(130,NULL,10,51),(131,'shoe/0E08116/褐色/shoe_image.jpg',9,51),(132,'shoe/0E19550/黑色/shoe_image.jpg',1,52),(133,'shoe/0E19550/褐色/shoe_image.jpg',9,52),(134,NULL,10,52),(135,NULL,1,53),(136,'shoe/0E19539/褐色/shoe_image.jpg',9,53),(137,NULL,10,53),(138,NULL,9,3),(139,'shoe/3E1122/驼色/shoe_image.jpg',10,3),(140,'shoe/2E0079/褐色/shoe_image.jpg',9,54),(141,NULL,10,54),(142,NULL,1,54),(143,NULL,1,55),(144,'shoe/C10031/棕色/shoe_image.jpg',3,55),(145,NULL,10,55),(146,'shoe/3E29511/黑色/shoe_image.jpg',1,56),(147,NULL,3,56),(148,NULL,10,56),(156,'shoe/3E12212-1/黑色/shoe_image.jpg',1,60),(157,'shoe/3E12212-1/驼色/shoe_image.jpg',10,60),(158,'shoe/JC3926Y-C357X/黑色/shoe_image.jpg',1,61),(164,'shoe/JC9263-E187/黑色/shoe_image.jpg',1,64),(165,'shoe/JC9263-E187/米色/shoe_image.jpg',6,64),(166,'shoe/JC9263-E187/驼色/shoe_image.jpg',10,64),(168,'shoe/5E0191-1/黑色/shoe_image.jpg',1,66),(169,NULL,10,66),(171,NULL,4,57),(172,'shoe/C60986/驼色/shoe_image.jpg',10,57),(173,NULL,3,57),(174,NULL,1,58),(175,'shoe/3E3061/驼色/shoe_image.jpg',10,58),(176,NULL,10,59),(177,NULL,15,59),(178,NULL,1,62),(179,'shoe/JC3926Y-C357/驼色/shoe_image.jpg',10,62),(180,NULL,1,63),(181,NULL,6,63),(182,'shoe/JC9263-E206/驼色/shoe_image.jpg',10,63),(183,NULL,1,65),(184,'shoe/JC2088-E205  电镀片/卡其色/shoe_image.jpg',16,65),(185,NULL,10,65),(186,NULL,16,66),(187,'shoe/JC8307-C398/黑色/shoe_image.jpg',1,67),(188,NULL,6,67),(189,'shoe/JC8307-E161/黑色/shoe_image.jpg',1,68),(190,'shoe/JC8307-E161/驼色/shoe_image.jpg',10,68),(191,'shoe/JC8307-E161/米色/shoe_image.jpg',6,68),(192,NULL,1,69),(193,NULL,16,69),(194,'shoe/JC2088-E161Z/米色/shoe_image.jpg',6,69),(195,'shoe/3E12213/黑色/shoe_image.jpg',1,70),(196,'shoe/3E12213/棕色/shoe_image.jpg',3,70),(197,NULL,1,71),(198,'shoe/JC2088-E61/卡其色/shoe_image.jpg',16,71),(199,'shoe/5E0211/黑色/shoe_image.jpg',1,72),(200,'shoe/5E0211/棕色/shoe_image.jpg',3,72),(201,'shoe/5E0211/驼色/shoe_image.jpg',10,72),(202,'shoe/JC8307-E208F/驼色/shoe_image.jpg',10,73),(203,'shoe/JC8307-E208F/卡其色/shoe_image.jpg',16,73),(204,'shoe/3E5161/黑色/shoe_image.jpg',1,74),(205,'shoe/3E5161/驼色/shoe_image.jpg',10,74),(206,'shoe/3E5161/棕色/shoe_image.jpg',3,74),(207,'shoe/5E0212/黑色/shoe_image.jpg',1,75),(208,'shoe/5E0212/棕色/shoe_image.jpg',3,75),(209,'shoe/5E0212/驼色/shoe_image.jpg',10,75),(210,'shoe/3E5166/黑色/shoe_image.jpg',1,76),(211,'shoe/3E5166/驼色/shoe_image.jpg',10,76),(212,'shoe/3E5166/棕色/shoe_image.jpg',3,76),(213,'shoe/3E30013/黑色/shoe_image.jpg',1,77),(214,'shoe/3E30013/驼色/shoe_image.jpg',10,77),(215,'shoe/3E30013/卡其色/shoe_image.jpg',16,77),(216,NULL,1,78),(217,NULL,16,78),(218,NULL,19,78),(219,'shoe/0E7315/黑色/shoe_image.jpg',1,79),(220,'shoe/0E7315/驼色/shoe_image.jpg',10,79),(221,'shoe/0E7315/棕色/shoe_image.jpg',3,79),(222,'shoe/0E17855/黑色/shoe_image.jpg',1,80),(223,'shoe/0E17855/驼色/shoe_image.jpg',10,80),(224,'shoe/0E17855/棕色/shoe_image.jpg',3,80),(225,NULL,1,81),(226,NULL,3,81),(227,'shoe/5E0251/米色/shoe_image.jpg',6,81),(228,NULL,1,82),(229,'shoe/5E0252/驼色/shoe_image.jpg',10,82),(230,NULL,6,82),(231,NULL,1,83),(232,'shoe/5E3671/驼色/shoe_image.jpg',10,83),(233,NULL,6,83),(234,NULL,1,84),(235,'shoe/5E3672/驼色/shoe_image.jpg',10,84),(236,NULL,6,84),(237,NULL,1,85),(238,'shoe/3E3318/卡其色/shoe_image.jpg',16,85),(239,NULL,1,86),(240,'shoe/3E3317/驼色/shoe_image.jpg',10,86),(241,'shoe/5E0261/黑色/shoe_image.jpg',1,87),(242,NULL,10,87),(243,'shoe/5E0263/黑色/shoe_image.jpg',1,88),(244,NULL,10,88),(245,NULL,1,89),(246,'shoe/5E0196/褐色/shoe_image.jpg',9,89),(247,NULL,1,90),(248,'shoe/2E01017/褐色/shoe_image.jpg',9,90),(249,'shoe/0E19556/褐色/shoe_image.jpg',9,91),(250,NULL,1,92),(251,'shoe/2E3776/褐色/shoe_image.jpg',9,92),(252,NULL,1,93),(253,'shoe/3E2565/驼色/shoe_image.jpg',10,93),(254,'shoe/0E21923/驼色/shoe_image.jpg',10,94),(255,'shoe/0E21936/黑色/shoe_image.jpg',1,95),(258,'shoe/0E21936/褐色/shoe_image.jpg',9,95),(260,'shoe/0E21928/黑色/shoe_image.jpg',1,96);
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
  `size_material_specification` varchar(40) NOT NULL DEFAULT '',
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
  `size_storage_type` char(10) NOT NULL DEFAULT 'E',
  `material_outsource_date` date DEFAULT NULL,
  `material_id` bigint NOT NULL,
  `size_material_color` varchar(40) DEFAULT '',
  `order_id` bigint DEFAULT NULL,
  `order_shoe_id` bigint DEFAULT NULL,
  `unit_price` decimal(10,2) DEFAULT NULL,
  `purchase_divide_order_id` bigint DEFAULT NULL,
  `material_estimated_arrival_date` date DEFAULT NULL,
  `size_material_model` varchar(40) DEFAULT '',
  `material_storage_status` tinyint DEFAULT NULL,
  `composite_unit_cost` decimal(10,2) DEFAULT NULL,
  `craft_name` varchar(200) DEFAULT NULL,
  `department_id` int DEFAULT NULL,
  `production_instruction_item_id` bigint DEFAULT NULL,
  PRIMARY KEY (`size_material_storage_id`),
  UNIQUE KEY `unq_size_material_storage` (`material_id`,`order_shoe_id`,`size_material_color`),
  KEY `fk_size_material_storage0` (`material_id`),
  KEY `fk_size_material_storage_color` (`size_material_color`),
  KEY `fk_size_material_storage` (`order_shoe_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `staff_status` int NOT NULL DEFAULT '0',
  `id_number` varchar(18) DEFAULT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `birth_date` date DEFAULT NULL,
  PRIMARY KEY (`staff_id`),
  KEY `fk_staffs_staffs` (`character_id`),
  KEY `fk_staffs_departments` (`department_id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff`
--

LOCK TABLES `staff` WRITE;
/*!40000 ALTER TABLE `staff` DISABLE KEYS */;
INSERT INTO `staff` VALUES (1,'吴启龙',14,9,0,NULL,NULL,NULL),(2,'总经理',2,8,0,NULL,NULL,NULL),(3,'谢树洼',9,6,0,NULL,NULL,NULL),(4,'黄培培',10,13,0,NULL,NULL,NULL),(5,'邹远东',6,4,0,NULL,NULL,NULL),(6,'豆德成',16,4,0,NULL,NULL,NULL),(7,'开发一部',7,11,0,NULL,NULL,NULL),(8,'孙汝满',7,11,0,NULL,NULL,NULL),(9,'舒克能',7,11,0,NULL,NULL,NULL),(10,'业务部经理1',4,10,0,NULL,NULL,NULL),(11,'范建明',8,12,0,NULL,NULL,NULL),(13,'潘璟',5,5,0,NULL,NULL,NULL),(14,'姜',18,11,0,NULL,NULL,NULL),(15,'技术部文员',17,5,0,NULL,NULL,NULL),(16,'生产副总',3,4,0,NULL,NULL,NULL),(17,'裁断',11,4,0,NULL,NULL,NULL),(18,'针车',12,4,0,NULL,NULL,NULL),(19,'成型',13,4,0,NULL,NULL,NULL),(20,'半成品',19,12,0,NULL,NULL,NULL),(21,'成品',20,12,0,NULL,NULL,NULL),(22,'业务部文员1',21,10,0,NULL,NULL,NULL),(23,'业务部文员2',21,10,0,NULL,NULL,NULL),(24,'业务部经理2',4,10,0,NULL,NULL,NULL),(25,'业务部文员3',21,10,0,NULL,NULL,NULL),(26,'业务部文员5',21,10,0,NULL,NULL,NULL),(27,'业务部文员6',21,10,0,NULL,NULL,NULL),(28,'业务部文员7',21,10,0,NULL,NULL,NULL),(29,'业务部文员8',21,10,0,NULL,NULL,NULL),(30,'业务部经理3',4,10,0,NULL,NULL,NULL),(31,'开发二部',7,14,0,NULL,NULL,NULL),(32,'开发三部',7,15,0,NULL,NULL,NULL);
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
) ENGINE=InnoDB AUTO_INCREMENT=222 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier`
--

LOCK TABLES `supplier` WRITE;
/*!40000 ALTER TABLE `supplier` DISABLE KEYS */;
INSERT INTO `supplier` VALUES (1,'询价','N'),(2,'采购员','N'),(3,'行政采购','N'),(4,'商务采购','N'),(5,'豪富达中底','N'),(6,'森达鞋楦','N'),(7,'昊宇鞋楦','N'),(8,'佳明粉胶','N'),(9,'科盛化工','N'),(10,'小东化工','N'),(11,'瓯海纸业','N'),(12,'珍和鞋盒','N'),(13,'阿其鞋盒','N'),(14,'阿孟鞋盒','N'),(15,'东鑫包装','N'),(16,'炜一刀模','N'),(17,'鸿达刀模','N'),(18,'华一线业','N'),(19,'灯塔线业','N'),(20,'卓玛鞋材','N'),(21,'秀莲鞋材','N'),(22,'旭东鞋材','N'),(23,'兴元印刷','N'),(24,'创辉底材','N'),(25,'日禾底材','N'),(26,'双泰底材','N'),(27,'大富豪底材','N'),(28,'汇丰鞋跟','N'),(29,'嘉泰皮革','N'),(30,'瑞佳皮革','N'),(31,'宝社皮革','N'),(32,'伟翔底材','N'),(33,'川东底材','N'),(34,'正东底材','N'),(35,'东莞鑫峰达底材','N'),(36,'一一鞋材','N'),(37,'秀莲鞋眼','N'),(38,'佳明针车行','N'),(39,'刘可蒙副食品','N'),(40,'胜国鞋扣','N'),(41,'宏锦皮革','N'),(42,'吉隆利发印刷厂','N'),(43,'福秀鞋材','N'),(44,'双榜拉链','N'),(45,'尚景饰扣','N'),(46,'瑞祥五金','N'),(47,'茂利皮革','N'),(48,'卓尔丝印板','N'),(49,'大丰鞋材','N'),(50,'嘉锦底材','N'),(51,'天塑皮革','N'),(52,'联创鞋材','N'),(53,'沃德利鞋材','N'),(54,'海龙皮毛','N'),(55,'君远纺织','N'),(56,'麦斯克条码','N'),(57,'曼凌鞋扣','N'),(58,'晴鑫鞋材','N'),(59,'润丰皮革','N'),(60,'宏锦皮革-东莞','N'),(61,'万锦纺织','N'),(62,'唯佳皮革','N'),(63,'鸿源皮革','N'),(64,'迦力底材','N'),(65,'约西底材','N'),(66,'广联底材','N'),(67,'万宇鞋材','N'),(68,'崎云布标','N'),(69,'和合拉链','N'),(70,'国茂皮革','N'),(71,'齐轩包装','N'),(72,'强大鞋材','N'),(73,'金凤中底厂','N'),(74,'顺达五金','N'),(75,'丰玲飞织','N'),(76,'福建义可底材','N'),(77,'东莞稳多多底材','N'),(78,'爱迪尔皮革','N'),(79,'齐雅皮革','N'),(80,'强锋皮革','N'),(81,'深源皮革','N'),(82,'海信皮标','N'),(83,'添鸿皮革','N'),(84,'登革路皮革','N'),(85,'南力化工','N'),(86,'瓯瑞皮革','N'),(87,'黄隆鞋机','N'),(88,'欧聚鞋材','N'),(89,'昊宇底材','N'),(90,'建斌鞋材','N'),(91,'华盛鞋盒','N'),(92,'东莞鸿泰鞋材','N'),(93,'申明鞋机','N'),(94,'永旭皮革','N'),(95,'惠东博泰皮革','N'),(96,'东日底材','N'),(97,'亿嘉皮革','N'),(98,'宏益皮业','N'),(99,'鑫福包装','N'),(100,'东莞骏华拉链','N'),(101,'远足鞋楦','N'),(102,'小安鞋底','N'),(103,'东莞林发鞋楦','N'),(104,'东莞冠鑫鞋材','N'),(105,'东莞悦盛鞋材','N'),(106,'惠东六合皮革','N'),(107,'深澳中底','N'),(108,'宏森皮革','N'),(109,'胜亮鞋材','N'),(110,'鞋艺笔业','N'),(111,'富昌织带','N'),(112,'沣进特材','N'),(113,'嘉隆底材','N'),(114,'方圆底材','N'),(115,'福建辉煌皮革','N'),(116,'创立底材','N'),(117,'博鑫鞋材','N'),(118,'三秦鞋跟','N'),(119,'保利特材','N'),(120,'东莞隆泰皮革','N'),(121,'新浪鞋跟','N'),(122,'胜丰皮业','N'),(123,'阿里皮业','N'),(124,'浙礼底材','N'),(125,'同人底材','N'),(126,'双禾皮革','N'),(127,'赛能皮革','N'),(128,'远鸿鞋材','N'),(129,'国星皮革','N'),(130,'中瑞中底','N'),(131,'风象鞋材','N'),(132,'阿里巴巴皮业','N'),(133,'鑫博底材','N'),(134,'汇鑫鞋模','N'),(135,'大丰收底材','N'),(136,'丰收针织','N'),(137,'晋江佐源底材','N'),(138,'泉州曾村底材','N'),(139,'华邦皮革','N'),(140,'齐业鞋材','N'),(141,'布凡鞋材','N'),(142,'网中网鞋材','N'),(143,'双峰底材','N'),(144,'谐和鞋材','N'),(145,'鹤羽底材','N'),(146,'京源皮革','N'),(147,'宏盛鞋材','N'),(148,'飞宇布业','N'),(149,'海景鞋材','N'),(150,'美帝皮革','N'),(151,'发发特材','N'),(152,'志坚鞋盒','N'),(153,'尼西皮革','N'),(154,'晟灏制袋','N'),(155,'东莞轩凯皮革','N'),(156,'千嘉亿皮业','N'),(157,'斯塔尔化工','N'),(158,'东莞正祺纺织','N'),(159,'东莞琪峰底材','N'),(160,'超颖鞋材','N'),(161,'东莞广艺鞋楦','N'),(162,'星圣皮革','N'),(163,'邦宏鞋材','N'),(164,'振奋底材','N'),(165,'东莞信辉皮革','N'),(166,'高崎机械','N'),(167,'旭都包装','N'),(168,'源祺鞋材','N'),(169,'意元鞋材','N'),(170,'宏毅达鞋材','N'),(171,'豪锦皮革','N'),(172,'宝莱皮革','N'),(173,'宝来皮革','N'),(174,'上品皮革','N'),(175,'忠良皮革','N'),(176,'晋江牛丝顿底材','N'),(177,'亿威底材','N'),(178,'嘉杰鞋楦','N'),(179,'米沙利服材','N'),(180,'正鸿皮革','N'),(181,'勇丰刀模','N'),(182,'晋江晟仁底材','N'),(183,'东莞君硕鞋材','N'),(184,'广州硕艺涵伊鞋材','N'),(185,'茶山工艺印刷厂','N'),(186,'克豪底材','N'),(187,'东印智造包装','N'),(188,'三友皮业','N'),(189,'兴欣复合','W'),(190,'富潮复合','W'),(191,'金乡加工','W'),(192,'康鸿加工','W'),(193,'创本鞋材','W'),(194,'阿春印花加工','W'),(195,'理想印花加工','W'),(196,'朱立东加工','W'),(197,'方平绣花加工','W'),(198,'阿军丝印','W'),(199,'鑫泽加工','W'),(200,'尹敬加工','W'),(201,'马旦激光加工','W'),(202,'源达加工','W'),(203,'阿强加工','W'),(204,'花蕾','W'),(205,'悦泰鞋材','W'),(206,'吴志丁加工','W'),(207,'鸿运鞋材','N'),(208,'深博','N'),(209,'自购',NULL),(210,'顺顺五金',NULL),(211,'',NULL),(212,'永顺鞋材',NULL),(213,'天宇鞋材',NULL),(214,'曼婈扣件',NULL),(215,'顺顺拉链',NULL),(216,'亿威鞋材',NULL),(217,'豪富中底',NULL),(218,'昊宇鞋材',NULL),(219,'福秀',NULL),(220,'浙礼',NULL),(221,'嘉泰',NULL);
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='status: \n0 saved, \n1 submitted, \n2 approved';
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
INSERT INTO `unit_price_report_detail` VALUES (1,1,'矮靴',0.47,'');
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
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'wuqilong','21232f297a57a5a743894a0e4a801fc3',1),(2,'generalmanager','21232f297a57a5a743894a0e4a801fc3',2),(3,'xieshuwa','acc1a36421f87d37dc26dbebdd0de10e',3),(5,'zhouwei','21232f297a57a5a743894a0e4a801fc3',7),(6,'technicalclerk','21232f297a57a5a743894a0e4a801fc3',15),(7,'jianglaoshi','21232f297a57a5a743894a0e4a801fc3',14),(8,'yewujingli1','e99ad9c52a5d22773ee4d626825e6d75',10),(9,'fanjianming','21232f297a57a5a743894a0e4a801fc3',11),(10,'zouyuandong','21232f297a57a5a743894a0e4a801fc3',5),(11,'panjing','21232f297a57a5a743894a0e4a801fc3',13),(12,'fuzong','21232f297a57a5a743894a0e4a801fc3',16),(13,'caiduan','21232f297a57a5a743894a0e4a801fc3',17),(14,'zhenche','21232f297a57a5a743894a0e4a801fc3',18),(15,'chengxing','21232f297a57a5a743894a0e4a801fc3',19),(16,'banchengpin','21232f297a57a5a743894a0e4a801fc3',20),(17,'chengpin','21232f297a57a5a743894a0e4a801fc3',21),(18,'yewubu1','8f5b7097b76bdfa6985cf95e1da5799b',22),(19,'yewujingli2','21232f297a57a5a743894a0e4a801fc3',24),(20,'yewubu2','21232f297a57a5a743894a0e4a801fc3',23),(21,'yewubu3','8b271aa574fa2ba381be7e9c47337c9f',25),(22,'yewubu4','9370e876ddb9eb99bbfaf2888f3f5547',26),(23,'yewubu5','21232f297a57a5a743894a0e4a801fc3',27),(24,'yewubu6','21232f297a57a5a743894a0e4a801fc3',28),(25,'yewubu7','21232f297a57a5a743894a0e4a801fc3',29),(26,'yewujingli3','21232f297a57a5a743894a0e4a801fc3',30),(27,'kaifabu1','21232f297a57a5a743894a0e4a801fc3',7),(28,'kaifabu2','21232f297a57a5a743894a0e4a801fc3',31),(29,'kaifabu3','21232f297a57a5a743894a0e4a801fc3',32),(30,'ceshi','21232f297a57a5a743894a0e4a801fc3',3);
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

-- Dump completed on 2025-01-04 21:59:58
