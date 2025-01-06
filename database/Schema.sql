-- Table: Customers
CREATE TABLE Customers (
    C_id INT PRIMARY KEY AUTO_INCREMENT,
    Member_id VARCHAR(45),
    Fname VARCHAR(45),
    Lname VARCHAR(45),
    Phone VARCHAR(15),
    Email VARCHAR(45),
    Address1 VARCHAR(45),
    Address2 VARCHAR(45),
    City VARCHAR(45),
    State CHAR(2),
    Zip INT,
    Altru_id VARCHAR(45)
);

-- Table: Events
CREATE TABLE Events (
    Event_ID INT PRIMARY KEY AUTO_INCREMENT,
    C_id INT,
    Name VARCHAR(45),
    EventDate DATE,
    FOREIGN KEY (C_id) REFERENCES Customers(C_id)
);

-- Table: Employees
CREATE TABLE Employees (
    E_id INT PRIMARY KEY AUTO_INCREMENT,
    Fname VARCHAR(45),
    Lname VARCHAR(15),
    Phone VARCHAR(15),
    Email VARCHAR(55)
);

-- Table: Departments
CREATE TABLE Departments (
    D_id INT PRIMARY KEY AUTO_INCREMENT,
    E_id INT,
    Name VARCHAR(45),
    FOREIGN KEY (E_id) REFERENCES Employees(E_id)
);

-- Table: Wristbands
CREATE TABLE Wristbands (
    W_id INT PRIMARY KEY AUTO_INCREMENT,
    Event_ID INT,
    Issued DATETIME,
    FOREIGN KEY (Event_ID) REFERENCES Events(Event_ID)
);

-- Table: ParkingPasses
CREATE TABLE ParkingPasses (
    PP_id INT PRIMARY KEY AUTO_INCREMENT,
    Event_ID INT,
    Issued DATETIME,
    FOREIGN KEY (Event_ID) REFERENCES Events(Event_ID)
);

-- Table: PassTypes
CREATE TABLE PassTypes (
    PT_id INT PRIMARY KEY AUTO_INCREMENT,
    PP_id INT,
    PassType VARCHAR(45),
    Cost DECIMAL(10, 2),
    FOREIGN KEY (PP_id) REFERENCES ParkingPasses(PP_id)
);
