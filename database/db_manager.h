#ifndef DB_MANAGER_H
#define DB_MANAGER_H

#ifdef __cplusplus
extern "C" {
#endif

int  db_init(void);
int  db_insert(float temperature_c, float humidity_pct);
int  db_count(void);
void db_stats(void);
void db_export_csv(const char *filename);
void db_close(void);

#ifdef __cplusplus
}
#endif

#endif
