#include <wiringPi.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>

#define DHT22_PIN 7

static int dht22_data[5] = {0, 0, 0, 0, 0};

static int read_dht22_raw(void)
{
    uint8_t last_state = HIGH;
    uint8_t counter    = 0;
    uint8_t j          = 0;
    uint8_t i;

    for (i = 0; i < 5; i++) {
        dht22_data[i] = 0;
    }

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
            if (counter > 16) {
                dht22_data[j / 8] |= 1;
            }
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

int dht22_read(float *temperature, float *humidity)
{
    if (read_dht22_raw() == 0) {
        return 0;
    }

    *humidity    = (float)((dht22_data[0] << 8) + dht22_data[1]) / 10.0f;
    *temperature = (float)(((dht22_data[2] & 0x7F) << 8) + dht22_data[3]) / 10.0f;

    if (dht22_data[2] & 0x80) {
        *temperature = -(*temperature);
    }

    return 1;
}

int main(int argc, char *argv[])
{
    float temperature = 0.0f;
    float humidity    = 0.0f;

    if (wiringPiSetup() == -1) {
        fprintf(stderr, "wiringPi の初期化に失敗しました\n");
        return 1;
    }

    printf("DHT22 温湿度センサー 読み取り開始 (Ctrl+C で停止)\n");

    for (;;) {
        if (dht22_read(&temperature, &humidity)) {
            printf("気温: %.1f C  |  湿度: %.1f %%\n", temperature, humidity);
        } else {
            printf("読み取り失敗（リトライ中...）\n");
        }
        delay(2000);
    }

    return 0;
}
