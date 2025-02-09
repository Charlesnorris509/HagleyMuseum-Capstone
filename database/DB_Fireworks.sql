--------------------------------------------------------------------
-- Script Name: DB_Fireworks.sql
-- Date Created: 01-22-2025
-- Database: FireworksDB
-- Description: Centralized Database for the Hagley Museum and 
--              library's Fireworks Event
--------------------------------------------------------------------
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE DATABASE IF NOT EXISTS FireworksDB DEFAULT CHARACTER SET utf8;
USE `FireworksDB`;
--------------------------------------------------------------------


--------------------------------------------------------------------
-- Table Creation
--------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `FireworksDB`.`Customers` (
  `C_id` INT NOT NULL auto_increment,
  `Member_id` VARCHAR(45) NULL,
  `MembershipLevel` VARCHAR(45) NULL,
  `Fname` VARCHAR(45) NOT NULL,
  `Lname` VARCHAR(45) NOT NULL,
  `Phone` VARCHAR(15) NOT NULL,
  `Email` VARCHAR(45) NOT NULL,
  `Address1` VARCHAR(45) NOT NULL,
  `Address2` VARCHAR(45) NULL,
  `City` VARCHAR(45) NOT NULL,
  `Zip` INT(5) NOT NULL,
  `State` CHAR(2) NOT NULL,
  `Attended` TINYINT NULL,
  `Paid` TINYINT NULL,
  `Cancelled` TINYINT NULL,
  PRIMARY KEY (`C_id`),
  UNIQUE INDEX `ID_UNIQUE` (`C_id` ASC) VISIBLE,
  UNIQUE INDEX `Member_id_UNIQUE` (`Member_id` ASC) VISIBLE)
ENGINE = InnoDB;



CREATE TABLE IF NOT EXISTS `FireworksDB`.`Employees` (
  `E_id` INT NOT NULL auto_increment,
  `Fname` VARCHAR(45) NULL,
  `Lname` VARCHAR(45) NULL,
  `Phone` VARCHAR(15) NULL,
  `Email` VARCHAR(45) NULL,
  PRIMARY KEY (`E_id`))
ENGINE = InnoDB;



CREATE TABLE IF NOT EXISTS `FireworksDB`.`Events` (
  `Event_ID` INT NOT NULL auto_increment,
  `C_id` INT NOT NULL,
  `E_id` INT NULL,
  `Name` VARCHAR(45) NOT NULL,
  `EventDate` DATE NOT NULL,
  PRIMARY KEY (`Event_ID`, `C_id`, `E_id`),
  UNIQUE INDEX `EventName_UNIQUE` (`Name` ASC) VISIBLE,
  UNIQUE INDEX `Event_ID_UNIQUE` (`Event_ID` ASC) VISIBLE,
  INDEX `fk_EventSales_Customers1_idx` (`C_id` ASC) VISIBLE,
  INDEX `fk_EventSales_Employees1_idx` (`E_id` ASC) VISIBLE,
  CONSTRAINT `fk_EventSales_Customers1`
    FOREIGN KEY (`C_id`)
    REFERENCES `FireworksDB`.`Customers` (`C_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_EventSales_Employees1`
    FOREIGN KEY (`E_id`)
    REFERENCES `FireworksDB`.`Employees` (`E_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



CREATE TABLE IF NOT EXISTS `FireworksDB`.`Wristbands` (
  `W_id` INT NOT NULL auto_increment,
  `Event_ID` INT NOT NULL,
  `Issued` DATETIME NULL,
  PRIMARY KEY (`W_id`, `Event_ID`),
  UNIQUE INDEX `W_ID_UNIQUE` (`W_id` ASC) VISIBLE,
  INDEX `fk_Wristbands_EventSales1_idx` (`Event_ID` ASC) VISIBLE,
  CONSTRAINT `fk_Wristbands_EventSales1`
    FOREIGN KEY (`Event_ID`)
    REFERENCES `FireworksDB`.`Events` (`Event_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



CREATE TABLE IF NOT EXISTS `FireworksDB`.`ParkingPasses` (
  `PP_id` INT NOT NULL auto_increment,
  `Event_ID` INT NOT NULL,
  `Issued` DATETIME NULL,
  PRIMARY KEY (`PP_id`),
  INDEX `fk_ParkingPasses_EventSales1_idx` (`Event_ID` ASC) VISIBLE,
  CONSTRAINT `fk_ParkingPasses_EventSales1`
    FOREIGN KEY (`Event_ID`)
    REFERENCES `FireworksDB`.`Events` (`Event_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



CREATE TABLE IF NOT EXISTS `FireworksDB`.`PassTypes` (
  `PT_id` INT NOT NULL auto_increment,
  `PP_id` INT NOT NULL,
  `PassTypes` VARCHAR(45) NOT NULL,
  `Cost` DECIMAL(10, 2) NOT NULL,
  PRIMARY KEY (`PT_id`, `PP_id`),
  INDEX `fk_PassTypes_ParkingPasses1_idx` (`PP_id` ASC) VISIBLE,
  CONSTRAINT `fk_PassTypes_ParkingPasses1`
    FOREIGN KEY (`PP_id`)
    REFERENCES `FireworksDB`.`ParkingPasses` (`PP_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `FireworksDB`.`Departments` (
  `D_id` INT NOT NULL auto_increment,
  `E_id` INT NOT NULL,
  `DName` VARCHAR(45) NULL,
  PRIMARY KEY (`D_id`, `E_id`),
  INDEX `fk_Departments_Employees1_idx` (`E_id` ASC) VISIBLE,
  CONSTRAINT `fk_Departments_Employees1`
    FOREIGN KEY (`E_id`)
    REFERENCES `FireworksDB`.`Employees` (`E_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

--------------------------------------------------------------------
-- Insert Statements
--------------------------------------------------------------------
/*
INSERT INTO FireworksDB.Customers (Member_id, MembershipLevel, Fname, Lname, Phone, Email, Address1, Address2, City, Zip, State, Attended, Paid, Cancelled) 
 

INSERT INTO FireworksDB.Employees (Fname, Lname, Phone, Email) 


INSERT INTO FireworksDB.Events (C_id, E_id, Name, EventDate) 


INSERT INTO FireworksDB.Wristbands (Event_ID, Issued) 


INSERT INTO FireworksDB.ParkingPasses (Event_ID, Issued) 


INSERT INTO FireworksDB.PassTypes (PP_id, PassTypes, Cost) 


INSERT INTO FireworksDB.Departments (E_id, DName) 

*/

--------------------------------------------------------------------
-- Trigger to limit parking passes
--------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER CheckPassLimitBeforeInsert
BEFORE INSERT ON FireworksDB.ParkingPasses
FOR EACH ROW
BEGIN
    DECLARE pass_count INT;
    DECLARE pass_limit INT;

    CASE 
        WHEN (SELECT PassTypes FROM FireworksDB.PassTypes WHERE PP_id = NEW.PP_id) = 'General' THEN
            SET pass_limit = 800;
        WHEN (SELECT PassTypes FROM FireworksDB.PassTypes WHERE PP_id = NEW.PP_id) = 'Premium' THEN
            SET pass_limit = 60;
        WHEN (SELECT PassTypes FROM FireworksDB.PassTypes WHERE PP_id = NEW.PP_id) = 'Catering' THEN
            SET pass_limit = 30;
		WHEN (SELECT PassTypes FROM FireworksDB.PassTypes WHERE PP_id = NEW.PP_id) = 'Buck Road' THEN
            SET pass_limit = 40;
        ELSE
            SET pass_limit = NULL; -- No limit for other types
    END CASE;

    IF pass_limit IS NOT NULL THEN
        SELECT COUNT(*)
        INTO pass_count
        FROM FireworksDB.ParkingPasses pp
        JOIN FireworksDB.PassTypes pt ON pp.PP_id = pt.PP_id
        WHERE pt.PassTypes = (SELECT PassTypes FROM FireworksDB.PassTypes WHERE PP_id = NEW.PP_id)
        AND pp.Event_ID = NEW.Event_ID;

        IF pass_count >= pass_limit THEN
            SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = CONCAT('Limit of ', pass_limit, ' ', 
								      (SELECT PassTypes FROM FireworksDB.PassTypes WHERE PP_id = NEW.PP_id), 
                                      ' passes sold for this event day.');
        END IF;
    END IF;
END$$

DELIMITER ;

--------------------------------------------------------------------
-- Procedures to determine how many Parking Passes are available.
--------------------------------------------------------------------

-- General
DELIMITER $$

CREATE PROCEDURE GetAvailableGeneralParkingPasses(
    IN p_EventID INT
)
BEGIN
    SELECT 800 - COUNT(PP_id) AS AvailableGeneralPasses
    FROM ParkingPasses
    WHERE Event_ID = p_EventID AND PP_id IN (SELECT PP_id FROM PassTypes WHERE PassTypes = 'General');
END$$

DELIMITER ;

-- Preimum Parking
DELIMITER $$

CREATE PROCEDURE GetAvailablePremiumParkingPasses(
    IN p_EventID INT
)
BEGIN
    SELECT 60 - COUNT(PP_id) AS AvailablePremiumPasses
    FROM ParkingPasses
    WHERE Event_ID = p_EventID AND PP_id IN (SELECT PP_id FROM PassTypes WHERE PassTypes = 'Premium');
END$$

DELIMITER ;
 
 -- Catering
 DELIMITER $$

CREATE PROCEDURE GetAvailableCateringParkingPasses(
    IN p_EventID INT
)
BEGIN
    SELECT 30 - COUNT(PP_id) AS AvailableCateringPasses
    FROM ParkingPasses
    WHERE Event_ID = p_EventID AND PP_id IN (SELECT PP_id FROM PassTypes WHERE PassTypes = 'Catering');
END$$

DELIMITER ;

-- Buck Road
DELIMITER $$

CREATE PROCEDURE GetAvailableBuckRoadParkingPasses(
    IN p_EventID INT
)
BEGIN
    SELECT 40 - COUNT(PP_id) AS AvailableBuckRoadPasses
    FROM ParkingPasses
    WHERE Event_ID = p_EventID AND PP_id IN (SELECT PP_id FROM PassTypes WHERE PassTypes = 'Buck Road');
END$$

DELIMITER ;




SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
