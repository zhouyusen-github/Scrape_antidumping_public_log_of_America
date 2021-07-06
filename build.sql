/*创建demo用户*/
create user demoKeyword identified by 'demoPassword';
GRANT ALL ON *.* TO 'demoKeyword'@'%';
flush privileges;
/* 如果用户已存在删除用户
drop user demoKeyword@'%';
flush privileges;
*/


/*建库*/
CREATE DATABASE IF NOT EXISTS `AD_CVD_data`;
USE `AD_CVD_data`;



/*建表*/
Drop table if exists `notice`;
Drop table if exists `rate`;
CREATE TABLE `notice` (
    `CaseID` varchar(50) NOT NULL COMMENT 'fromuuid',
    `ITCNo` varchar(50) DEFAULT NULL COMMENT '',
    `source_DOCNo` varchar(50) DEFAULT NULL COMMENT '',
    `notice_DOCNo` varchar(50) DEFAULT NULL COMMENT '',
    `Year` varchar(50) DEFAULT NULL COMMENT '',
    `Month` varchar(50) DEFAULT NULL COMMENT '',
    `Date` varchar(50) DEFAULT NULL COMMENT '',
    `ProducerID` varchar(50) DEFAULT NULL COMMENT '',
    `Action` varchar(50) DEFAULT NULL COMMENT '',
    `source_AD_CVD` varchar(50) DEFAULT NULL COMMENT '',
    `notice_AD_CVD` varchar(50) DEFAULT NULL COMMENT '',
    `Product` varchar(50) DEFAULT NULL COMMENT '',
    `source_Country` varchar(50) DEFAULT NULL COMMENT '',
    `notice_Country` varchar(50) DEFAULT NULL COMMENT '',
    `source` varchar(500) DEFAULT NULL COMMENT 'notice_url',
    `fed_reg` varchar(50) DEFAULT NULL COMMENT '',
    `Notes` varchar(50) DEFAULT NULL COMMENT '',
    `Petitioner_and_AltNm_list` varchar(500) DEFAULT NULL COMMENT '',
    `HS_list` varchar(1000) DEFAULT NULL COMMENT '',
    PRIMARY KEY (`CaseID`)
) ENGINE=INNODB DEFAULT CHARSET=UTF8MB4 COLLATE = UTF8MB4_BIN COMMENT='';


CREATE TABLE `rate` (
    `RateID` varchar(50) NOT NULL COMMENT 'fromuuid',
    `CaseID` varchar(50) DEFAULT NULL COMMENT '',
    `Exporter` varchar(1000) DEFAULT NULL COMMENT '',
    `ExpAltNm` varchar(50) DEFAULT NULL COMMENT 'Exporter缩写',
    `Producer` varchar(1000) DEFAULT NULL COMMENT '',
    `PdAltNm` varchar(50) DEFAULT NULL COMMENT 'Producer缩写',
    `CashDeposit` varchar(50) DEFAULT NULL COMMENT '',
    `DumpingMargin` varchar(50) DEFAULT NULL COMMENT '',
    `SubsidyRate` varchar(50) DEFAULT NULL COMMENT '',
    `AD_CVD` varchar(50) DEFAULT NULL COMMENT '',
    PRIMARY KEY (`RateID`)
) ENGINE=INNODB DEFAULT CHARSET=UTF8MB4 COLLATE = UTF8MB4_BIN COMMENT='';
