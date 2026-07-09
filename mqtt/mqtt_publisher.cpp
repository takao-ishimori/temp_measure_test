#include <wiringPi.h>
#include <mosquitto.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>

#define DHT22_PIN 7
#define TRIG_PIN  4
#define ECHO_PIN  5
#define BROKER    "localhost"
#define PORT      1883

static int dht22_data[5] = {0, 0, 0, 0, 0};
static struct mosquitto *mosq = NULL;

static int read_dht22_raw(void)
{
    uint8_t last_state = HIGH;
    uint8_t counter    = 0;
    uint8_t j          = 0;
    uint8_t i;

    for (i = 0; i < 5; i++) dht22_data[i] = 0;

    pinMode(DHT22_PIN, OUTPUT);
    digitalWrite(DHT22_PIN, LOW);
    delay(18);
    digitalWrite(DHT22_PIN, HIGH);
    delayMicroseconds(40);
    pinMode(DHT22_PIN, INPUT);

    for (i = 0; i < 85; i++) {
        counter = 0;
        while (digitalRead(DHT22_PIN) == last_state) {
            counter++;
            delayMicroseconds(1);
            if (counter == 255) break;
        }
        last_state = digitalRead(DHT22_PIN);
        if (counter == 255) break;

        if ((i >= 4) && (i % 2 == 0)) {
            dht22_data[j / 8] <<= 1;
            if (counter > 16) dht22_data[j / 8] |= 1;
            j++;
        }
    }

    if ((j >= 40) &&
        (dht22_data[4] == ((dht22_data[0] + dht22_data[1] +
                            dht22_data[2] + dht22_data[3]) & 0xFF))) {
        return 1;
    }
    return 0;
}

static float measure_distance(void)
{
    unsigned int start_time = 0;
    unsigned int end_time   = 0;
    unsigned int timeout    = 0;

    digitalWrite(TRIG_PIN, LOW);
    delay(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);

    timeout = 50000;
    while (digitalRead(ECHO_PIN) == LOW)
        if (--timeout == 0) return -1.0f;
    start_time = micros();

    timeout = 50000;
    while (digitalRead(ECHO_PIN) == HIGH)
        if (--timeout == 0) return -1.0f;
    end_time = micros();

    return (float)(end_time - start_time) / 58.0f;
}

int main(int argc, char *argv[])
{
    if (wiringPiSetup() == -1) {
        fprintf(stderr, "wiringPi 初期化失敗\n");
        return 1;
    }

    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    digitalWrite(TRIG_PIN, LOW);

    mosquitto_lib_init();
    mosq = mosquitto_new("dht22_publisher", 1, NULL);
    if (!mosq || mosquitto_connect(mosq, BROKER, PORT, 60) != MOSQ_ERR_SUCCESS) {
        fprintf(stderr, "MQTT ブローカー接続失敗\n");
        return 1;
    }
    mosquitto_loop_start(mosq);

    printf("MQTT パブリッシャー 開始 (Ctrl+C で停止)\n");

    char payload[64];

    for (;;) {
        if (read_dht22_raw()) {
            float t = (float)(((dht22_data[2] & 0x7F) << 8) + dht22_data[3]) / 10.0f;
            float h = (float)((dht22_data[0] << 8) + dht22_data[1]) / 10.0f;
            if (dht22_data[2] & 0x80) t = -t;

            snprintf(payload, sizeof(payload),
                     "{\"value\": %.1f, \"unit\": \"C\"}", t);
            mosquitto_publish(mosq, NULL, "sensor/temperature",
                              (int)strlen(payload), payload, 0, 0);

            snprintf(payload, sizeof(payload),
                     "{\"value\": %.1f, \"unit\": \"%%\"}", h);
            mosquitto_publish(mosq, NULL, "sensor/humidity",
                              (int)strlen(payload), payload, 0, 0);

            printf("気温: %.1f C  |  湿度: %.1f %%  → 送信完了\n", t, h);
        } else {
            printf("読み取り失敗（リトライ中...）\n");
        }

        float dist = measure_distance();
        if (dist >= 0.0f && dist <= 400.0f) {
            snprintf(payload, sizeof(payload),
                     "{\"value\": %.1f, \"unit\": \"cm\"}", dist);
            mosquitto_publish(mosq, NULL, "sensor/distance",
                              (int)strlen(payload), payload, 0, 0);
            printf("距離: %.1f cm  → 送信完了\n", dist);
        }

        delay(2000);
    }

    mosquitto_loop_stop(mosq, 0);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    return 0;
}
