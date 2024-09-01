#include <HID.h>
#include <Mouse.h>
#include <hiduniversal.h>
#include "hidmouserptparser.h"
#include "WiFiS3.h"

const char* SSID = "Naughty Nigel";    // Network SSID (name)
const char* PASS = "SharingIsCaring";    // Network PASSword (use for WPA, or use as key for WEP)

int status = WL_IDLE_STATUS;
int port = 50123;
int x = 0;
int y = 0;
String cmd = "";
char symbols[] = "-,0123456789";
char code[] = "SKIPPYCYPHER";
bool encrypt = false;
bool busy = false;

WiFiServer server(port);
USB Usb;
HIDUniversal Hid(&Usb);
HIDMouseReportParser Mou(nullptr);

void decryptCommand(String &command) {
  if (encrypt) {
    for (int i = 0; i < command.length(); i++) {
      for (int j = 0; j < sizeof(code) - 1; j++) {
        if (command[i] == code[j]) {
          command[i] = symbols[j];
          break;
        }
      }
    }
  }
}

WiFiClient client;

void setup() {
  //pinMode(LED_BUILTIN, OUTPUT);

  Mouse.begin();
	Serial.begin(115200);
	Serial.println("Start");

	if (Usb.Init() == -1)
		Serial.println("OSC did not start.");
	
	delay(200);

	if (!Hid.SetReportParser(0, &Mou))
		ErrorMessage<uint8_t > (PSTR("SetReportParser"), 1);

  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    // don't continue
    while (true);
  }

  // attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("trying to connect");
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(SSID, PASS);

    delay(1000);

    digitalWrite(LED_BUILTIN, HIGH);

    delay(1000);
  }
  server.begin();
  //digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("connected");
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
}

void loop() {
  Usb.Task();
  
  if (!client || !client.connected()) {
    client = server.available();
  }

  while (client.connected()) {
    Usb.Task();

    String cmd = client.readStringUntil('\r');
    Serial.println(cmd);

    if (cmd.length() > 0) {
      busy = true;

      if (cmd[0] == 'M') {
        decryptCommand(cmd);
        int commaIndex = cmd.indexOf(',');
        if (commaIndex != -1) {
          x = cmd.substring(1, commaIndex).toInt();
          y = cmd.substring(commaIndex + 1).toInt();

          while (x != 0 || y != 0) {
            int moveX = constrain(x, -128, 127);
            int moveY = constrain(y, -128, 127);

            Mouse.move(moveX, moveY);

            x -= moveX;
            y -= moveY;
          }
        }
      } else if (cmd[0] == 'C') {
        int randomDelay = random(40, 80);
        Mouse.press(MOUSE_LEFT);
        delay(randomDelay);
        Mouse.release(MOUSE_LEFT);
      } else if (cmd[0] == 'B') {
        if (cmd[1] == '1') {
          Mouse.press(MOUSE_LEFT);
        } else if (cmd[1] == '0') {
          Mouse.release(MOUSE_LEFT);
        }
      }
      client.print("a\r\n");
      client.flush();
    }
    else {
      busy = false;
    }
  }
  delay(1);
}

void onButtonDown(uint16_t buttonId) {
	Mouse.press(buttonId);
}

void onButtonUp(uint16_t buttonId) {
	Mouse.release(buttonId);
}

void onTiltPress(int8_t tiltValue) {
}

void onMouseMove(int8_t xMovement, int8_t yMovement, int8_t scrollValue) {
	Mouse.move(xMovement, yMovement, scrollValue);
}