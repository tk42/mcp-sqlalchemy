-- init.sql
-- データベースの作成
CREATE DATABASE MCPDatabase;
GO

USE MCPDatabase;
GO

-- クエリ履歴テーブル
CREATE TABLE query_history (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    query_text NVARCHAR(MAX),
    transformed_query NVARCHAR(MAX),
    execution_result NVARCHAR(MAX),
    error_message NVARCHAR(MAX),
    execution_time FLOAT,
    success BIT,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- インデックスの作成
CREATE INDEX idx_query_history_created_at ON query_history(created_at);
CREATE INDEX idx_query_history_success ON query_history(success);

-- メタデータテーブル
CREATE TABLE mcp_metadata (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    table_name NVARCHAR(128),
    column_name NVARCHAR(128),
    data_type NVARCHAR(128),
    description NVARCHAR(MAX),
    sample_values NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- パフォーマンスモニタリングテーブル
CREATE TABLE performance_metrics (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    query_id BIGINT,
    cpu_time BIGINT,
    elapsed_time BIGINT,
    logical_reads BIGINT,
    physical_reads BIGINT,
    row_count BIGINT,
    execution_plan XML,
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (query_id) REFERENCES query_history(id)
);

-- パーティション関数の作成（日付ベース）
CREATE PARTITION FUNCTION PF_QueryHistory_Date (DATETIME2)
AS RANGE RIGHT FOR VALUES (
    '2024-01-01', '2024-04-01', '2024-07-01', '2024-10-01',
    '2025-01-01', '2025-04-01', '2025-07-01', '2025-10-01'
);
GO

-- パーティションスキーマの作成
CREATE PARTITION SCHEME PS_QueryHistory_Date
AS PARTITION PF_QueryHistory_Date
ALL TO ([PRIMARY]);
GO

-- ストアドプロシージャ: クエリ履歴のクリーンアップ
CREATE PROCEDURE sp_cleanup_query_history
    @days_to_keep INT = 30
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @cutoff_date DATETIME2 = DATEADD(DAY, -@days_to_keep, GETDATE());
    
    BEGIN TRANSACTION;
    
    DELETE FROM performance_metrics
    WHERE query_id IN (
        SELECT id FROM query_history
        WHERE created_at < @cutoff_date
    );
    
    DELETE FROM query_history
    WHERE created_at < @cutoff_date;
    
    COMMIT TRANSACTION;
END;
GO

-- ジョブの作成: 自動クリーンアップ
-- Note: SQLServerエージェントが必要です
EXEC msdb.dbo.sp_add_job
    @job_name = N'Cleanup Query History',
    @enabled = 1,
    @description = N'Automatically cleanup old query history records';
GO

EXEC msdb.dbo.sp_add_jobstep
    @job_name = N'Cleanup Query History',
    @step_name = N'Execute Cleanup',
    @subsystem = N'TSQL',
    @command = N'EXEC sp_cleanup_query_history @days_to_keep = 30';
GO

EXEC msdb.dbo.sp_add_jobschedule
    @job_name = N'Cleanup Query History',
    @name = N'Daily Cleanup',
    @freq_type = 4,
    @freq_interval = 1,
    @active_start_time = 010000;
GO

-- 統計情報の自動更新設定
ALTER DATABASE MCPDatabase
SET AUTO_UPDATE_STATISTICS ON;
GO

ALTER DATABASE MCPDatabase
SET AUTO_UPDATE_STATISTICS_ASYNC ON;
GO

-- メモリ設定の最適化
EXEC sys.sp_configure 'show advanced options', 1;
GO
RECONFIGURE;
GO

EXEC sys.sp_configure 'max server memory (MB)', 8192;
GO
RECONFIGURE;
GO

-- MAXDOPの設定
EXEC sys.sp_configure 'max degree of parallelism', 4;
GO
RECONFIGURE;
GO

-- サンプルデータベースの作成
CREATE DATABASE SampleDB;
GO

USE SampleDB;
GO

-- 従業員テーブルの作成
CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY IDENTITY(1,1),
    FirstName NVARCHAR(50),
    LastName NVARCHAR(50),
    Department NVARCHAR(50),
    Position NVARCHAR(50),
    Salary DECIMAL(10,2),
    HireDate DATE
);
GO

-- 部署テーブルの作成
CREATE TABLE Departments (
    DepartmentID INT PRIMARY KEY IDENTITY(1,1),
    DepartmentName NVARCHAR(50),
    Location NVARCHAR(100),
    Budget DECIMAL(15,2)
);
GO

-- プロジェクトテーブルの作成
CREATE TABLE Projects (
    ProjectID INT PRIMARY KEY IDENTITY(1,1),
    ProjectName NVARCHAR(100),
    StartDate DATE,
    EndDate DATE,
    Budget DECIMAL(15,2),
    Status NVARCHAR(20)
);
GO

-- サンプルデータの挿入
INSERT INTO Departments (DepartmentName, Location, Budget) VALUES
    (N'開発部', N'東京', 50000000.00),
    (N'営業部', N'大阪', 30000000.00),
    (N'人事部', N'名古屋', 20000000.00);
GO

INSERT INTO Employees (FirstName, LastName, Department, Position, Salary, HireDate) VALUES
    (N'太郎', N'山田', N'開発部', N'シニアエンジニア', 6500000.00, '2020-04-01'),
    (N'花子', N'鈴木', N'営業部', N'営業マネージャー', 5500000.00, '2019-06-15'),
    (N'一郎', N'佐藤', N'人事部', N'人事マネージャー', 5000000.00, '2021-01-10'),
    (N'美咲', N'田中', N'開発部', N'プログラマー', 4500000.00, '2022-03-01'),
    (N'健一', N'高橋', N'営業部', N'営業担当', 4000000.00, '2023-07-01');
GO

INSERT INTO Projects (ProjectName, StartDate, EndDate, Budget, Status) VALUES
    (N'次世代CRMシステム開発', '2024-01-01', '2024-12-31', 30000000.00, N'進行中'),
    (N'モバイルアプリ開発', '2024-03-01', '2024-08-31', 15000000.00, N'計画中'),
    (N'データ分析基盤構築', '2024-02-01', '2024-06-30', 20000000.00, N'進行中');
GO