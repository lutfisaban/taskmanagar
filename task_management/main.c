#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>

#pragma comment(lib, "ws2_32.lib")
#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 8000
#define BUFFER_SIZE 1024

int should_continue(const char *message) {
    const char *success_or_error_messages[] = {
        "Sign up successful!",
        "Username already exists. Try again.",
        "Login successful!",
        "Task added successfully!",
        "No tasks found.",
        "No tasks for today.",
        "No tasks for",
        "Logged out.",
        "Invalid credentials. Try again.",
        "The Tasks:"
    };
    for (int i = 0; i < sizeof(success_or_error_messages) / sizeof(success_or_error_messages[0]); i++) {
        if (strstr(message, success_or_error_messages[i]) != NULL) {
            return 1;
        }
    }
    return 0;
}

int main() {
    WSADATA wsa;
    SOCKET client_socket;
    struct sockaddr_in server_addr;
    char buffer[BUFFER_SIZE];
    char user_input[BUFFER_SIZE];

    printf("Initializing Winsock...\n");
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        printf("Failed. Error Code: %d\n", WSAGetLastError());
        return 1;
    }
    printf("Winsock initialized.\n");

    if ((client_socket = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET) {
        printf("Socket creation failed. Error Code: %d\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    int timeout = 30000; // 30 seconds in milliseconds
    if (setsockopt(client_socket, SOL_SOCKET, SO_RCVTIMEO, (const char *)&timeout, sizeof(timeout)) < 0) {
        printf("Failed to set socket options. Error Code: %d\n", WSAGetLastError());
        closesocket(client_socket);
        WSACleanup();
        return 1;
    }


    server_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);

    printf("Connecting to the server...\n");
    if (connect(client_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        printf("Connection failed. Error Code: %d\n", WSAGetLastError());
        closesocket(client_socket);
        WSACleanup();
        return 1;
    }
    printf("Connected to the server.\n");

    while (1) {
        int bytes_received = recv(client_socket, buffer, BUFFER_SIZE - 1, 0);
        if (bytes_received == SOCKET_ERROR) {
            printf("Receive failed. Error Code: %d\n", WSAGetLastError());
            break;
        }

        buffer[bytes_received] = '\0';
        printf("%s", buffer);

        if (!should_continue(buffer)) {
            printf("> ");
            fgets(user_input, BUFFER_SIZE, stdin);
            user_input[strcspn(user_input, "\n")] = '\0'; // Remove newline character

            if (send(client_socket, user_input, strlen(user_input), 0) == SOCKET_ERROR) {
                printf("Send failed. Error Code: %d\n", WSAGetLastError());
                break;
            }
        } else {
            printf("\n");
        }

        if (strstr(buffer, "Logged out.") != NULL) {
            printf("Disconnecting...\n");
            break;
        }
    }

    closesocket(client_socket);
    WSACleanup();
    return 0;
}
