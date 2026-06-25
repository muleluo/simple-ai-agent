import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 简化的测试气泡
Rectangle {
    width: 600
    height: 400
    color: "#f8fafc"

    Column {
        anchors.centerIn: parent
        spacing: 20

        // 测试 1: 用户消息
        Rectangle {
            width: 300
            height: 80
            color: "#2563eb"
            radius: 12

            Text {
                anchors.centerIn: parent
                text: "用户消息测试"
                font.pixelSize: 14
                color: "white"
            }
        }

        // 测试 2: AI 消息
        Rectangle {
            width: 300
            height: 80
            color: "#ffffff"
            radius: 12
            border.width: 1
            border.color: "#e2e8f0"

            Text {
                anchors.centerIn: parent
                text: "AI 消息测试"
                font.pixelSize: 14
                color: "#1e293b"
            }
        }

        // 测试 3: 系统消息
        Rectangle {
            width: 200
            height: 50
            color: "#f1f5f9"
            radius: 8

            Text {
                anchors.centerIn: parent
                text: "系统消息测试"
                font.pixelSize: 14
                color: "#1e293b"
            }
        }
    }
}
