#include "db_manager.h"
#include <sqlite3.h>
#include <stdio.h>
#include <stdlib.h>
#include <cmath>

#define DB_PATH "database/dht22_data.db"

static sqlite3 *db = NULL;

int db_init(void)
{
    int rc = sqlite3_open(DB_PATH, &db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "DBオープン失敗: %s\n", sqlite3_errmsg(db));
        return 0;
    }

    const char *sql =
        "CREATE TABLE IF NOT EXISTS dht22_readings ("
        "  id            INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  timestamp     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),"
        "  temperature_c REAL    NOT NULL,"
        "  humidity_pct  REAL    NOT NULL"
        ");"
        "CREATE INDEX IF NOT EXISTS idx_timestamp ON dht22_readings(timestamp);";

    char *err = NULL;
    rc = sqlite3_exec(db, sql, NULL, NULL, &err);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "テーブル作成失敗: %s\n", err);
        sqlite3_free(err);
        return 0;
    }
    return 1;
}

int db_insert(float temperature_c, float humidity_pct)
{
    float t = std::roundf(temperature_c * 10.0f) / 10.0f;
    float h = std::roundf(humidity_pct  * 10.0f) / 10.0f;

    const char *sql =
        "INSERT INTO dht22_readings (temperature_c, humidity_pct) VALUES (?, ?);";
    sqlite3_stmt *stmt = NULL;

    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) return 0;

    sqlite3_bind_double(stmt, 1, t);
    sqlite3_bind_double(stmt, 2, h);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE) ? 1 : 0;
}

int db_count(void)
{
    sqlite3_stmt *stmt = NULL;
    sqlite3_prepare_v2(db, "SELECT COUNT(*) FROM dht22_readings;", -1, &stmt, NULL);
    sqlite3_step(stmt);
    int count = sqlite3_column_int(stmt, 0);
    sqlite3_finalize(stmt);
    return count;
}

void db_stats(void)
{
    printf("\n===== 統計 =====\n");
    printf("総データ数: %d 件\n", db_count());

    const char *sql =
        "SELECT AVG(temperature_c), MIN(temperature_c), MAX(temperature_c),"
        "       AVG(humidity_pct), MIN(humidity_pct), MAX(humidity_pct) "
        "FROM dht22_readings;";

    sqlite3_stmt *stmt = NULL;
    sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        printf("温度 平均: %.2f  最小: %.2f  最大: %.2f (C)\n",
               sqlite3_column_double(stmt, 0),
               sqlite3_column_double(stmt, 1),
               sqlite3_column_double(stmt, 2));
        printf("湿度 平均: %.2f  最小: %.2f  最大: %.2f (%%)\n",
               sqlite3_column_double(stmt, 3),
               sqlite3_column_double(stmt, 4),
               sqlite3_column_double(stmt, 5));
    }
    sqlite3_finalize(stmt);
}

void db_export_csv(const char *filename)
{
    FILE *fp = fopen(filename, "w");
    if (!fp) {
        fprintf(stderr, "CSVファイル作成失敗: %s\n", filename);
        return;
    }

    fprintf(fp, "id,timestamp,temperature_c,humidity_pct\n");

    const char *sql =
        "SELECT id, timestamp, temperature_c, humidity_pct "
        "FROM dht22_readings ORDER BY id;";
    sqlite3_stmt *stmt = NULL;
    sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        fprintf(fp, "%d,%s,%.1f,%.1f\n",
                sqlite3_column_int(stmt, 0),
                sqlite3_column_text(stmt, 1),
                sqlite3_column_double(stmt, 2),
                sqlite3_column_double(stmt, 3));
        count++;
    }
    sqlite3_finalize(stmt);
    fclose(fp);
    printf("CSV出力完了: %s  (%d 件)\n", filename, count);
}

void db_close(void)
{
    if (db) {
        sqlite3_close(db);
        db = NULL;
    }
}
