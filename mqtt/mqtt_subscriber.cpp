#include <mosquitto.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include "db_manager.h"

static struct mosquitto *mosq = NULL;
static volatile int running = 1;
static float latest_temp = -999.0f;
static float latest_hum  = -999.0f;
static int count = 0;

static void sig_handler(int sig)
{
    (void)sig;
    running = 0;
}

static void on_connect(struct mosquitto *m, void *ud, int rc)
{
    (void)ud;
    printf("MQTT ブローカーに接続 (rc=%d)\n", rc);
    mosquitto_subscribe(m, NULL, "sensor/temperature", 0);
    mosquitto_subscribe(m, NULL, "sensor/humidity", 0);
    mosquitto_subscribe(m, NULL, "sensor/distance", 0);
}

static void on_message(struct mosquitto *m, void *ud, const struct mosquitto_message *msg)
{
    (void)m;
    (void)ud;

    char *value_str = strchr((char *)msg->payload, ':');
    if (!value_str) return;
    value_str += 2;
    float value = atof(value_str);

    count++;
    printf("[%4d] %s = %.1f\n", count, msg->topic, value);

    if (strcmp(msg->topic, "sensor/temperature") == 0) {
        latest_temp = value;
    } else if (strcmp(msg->topic, "sensor/humidity") == 0) {
        latest_hum = value;
    }

    if (latest_temp > -900.0f && latest_hum > -900.0f) {
        db_insert(latest_temp, latest_hum);
        printf("          -> DB保存完了 (%.1f C, %.1f %%)\n", latest_temp, latest_hum);
        latest_temp = -999.0f;
        latest_hum  = -999.0f;
    }
}

int main(int argc, char *argv[])
{
    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    if (!db_init()) {
        fprintf(stderr, "DB初期化失敗\n");
        return 1;
    }

    mosquitto_lib_init();
    mosq = mosquitto_new("dht22_subscriber", 1, NULL);
    if (!mosq) {
        fprintf(stderr, "mosquitto初期化失敗\n");
        return 1;
    }

    mosquitto_connect_callback_set(mosq, on_connect);
    mosquitto_message_callback_set(mosq, on_message);

    if (mosquitto_connect(mosq, "localhost", 1883, 60) != MOSQ_ERR_SUCCESS) {
        fprintf(stderr, "MQTT ブローカー接続失敗\n");
        return 1;
    }

    printf("MQTT サブスクライバー(C++) 開始 (Ctrl+C で停止)\n");

    mosquitto_loop_start(mosq);

    while (running) {
        usleep(100000);
    }

    mosquitto_loop_stop(mosq, 0);
    mosquitto_disconnect(mosq);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    db_close();
    printf("\n停止しました\n");
    return 0;
}
