import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

// 消息气泡组件
Item {
    id: root
    property var messageData

    height: bubble.height

    // 根据发送者决定对齐方式
    readonly property bool isUser: messageData.sender === "user"
    readonly property bool isSystem: messageData.sender === "system"

    Rectangle {
        id: bubble
        // 系统消息居中显示，用户消息右对齐，AI 消息左对齐
        anchors.horizontalCenter: isSystem ? parent.horizontalCenter : undefined
        anchors.left: (isUser || isSystem) ? undefined : parent.left
        anchors.right: isUser ? parent.right : undefined
        anchors.leftMargin: (isUser || isSystem) ? undefined : 0
        anchors.rightMargin: isUser ? 0 : undefined

        // 直接设置最大宽度，让内部内容自适应
        implicitWidth: bubbleContent.implicitWidth + (isSystem ? 16 : 32)
        implicitHeight: bubbleContent.implicitHeight + (isSystem ? 16 : 32)
        width: Math.min(implicitWidth, isSystem ? parent.width * 0.6 : parent.width * 0.8)
        height: implicitHeight

        radius: isSystem ? 8 : 12

        // 背景颜色
        color: {
            if (isSystem) return "#f1f5f9"  // 系统消息灰色
            if (isUser) return "#2563eb"     // 用户消息蓝色
            return "#ffffff"                 // AI 消息白色
        }

        // 边框
        border.width: isUser || isSystem ? 0 : 1
        border.color: "#e2e8f0"

        // 阴影效果（使用 DropShadow）
        layer.enabled: !isSystem
        layer.effect: DropShadow {
            horizontalOffset: 0
            verticalOffset: 2
            radius: 8
            samples: 17
            color: "#20000000"
            transparentBorder: true
        }

        // 出现动画
        opacity: 0
        scale: 0.9

        Component.onCompleted: {
            appearAnimation.start()
        }

        ParallelAnimation {
            id: appearAnimation
            NumberAnimation {
                target: bubble
                property: "opacity"
                from: 0
                to: 1
                duration: 300
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                target: bubble
                property: "scale"
                from: 0.9
                to: 1.0
                duration: 300
                easing.type: Easing.OutBack
            }
        }

        ColumnLayout {
            id: bubbleContent
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: isSystem ? 8 : 16
            spacing: isSystem ? 4 : 8

            // 发送者标签（系统消息不显示）
            Text {
                visible: !isSystem
                text: {
                    if (isUser) return "你"
                    return "AI"
                }
                font.pixelSize: 11
                font.weight: Font.Medium
                color: {
                    if (isUser) return "rgba(255, 255, 255, 0.8)"
                    return "#64748b"
                }
                Layout.fillWidth: true
            }

            // 消息内容
            Text {
                id: messageText
                text: messageData.content
                font.pixelSize: 14
                color: isUser ? "white" : "#1e293b"
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
                Layout.fillWidth: true
                Layout.preferredWidth: Math.min(implicitWidth, isSystem ? (root.width * 0.6 - 32) : (root.width * 0.8 - 32))
            }

            // 时间戳（系统消息不显示）
            Text {
                visible: !isSystem
                text: messageData.timestamp
                font.pixelSize: 10
                color: {
                    if (isUser) return "rgba(255, 255, 255, 0.6)"
                    return "#94a3b8"
                }
                Layout.alignment: Qt.AlignRight
            }
        }

        // 三角指示器（可选）
        Canvas {
            visible: !isSystem
            anchors.left: isUser ? undefined : parent.left
            anchors.right: isUser ? parent.right : undefined
            anchors.top: parent.top
            anchors.topMargin: 12
            anchors.leftMargin: isUser ? undefined : -8
            anchors.rightMargin: isUser ? -8 : undefined

            width: 10
            height: 10

            // 监听颜色变化，重新绘制
            Connections {
                target: bubble
                function onColorChanged() {
                    requestPaint()
                }
            }

            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = bubble.color

                ctx.beginPath()
                if (isUser) {
                    ctx.moveTo(10, 0)
                    ctx.lineTo(0, 5)
                    ctx.lineTo(10, 10)
                } else {
                    ctx.moveTo(0, 0)
                    ctx.lineTo(10, 5)
                    ctx.lineTo(0, 10)
                }
                ctx.closePath()
                ctx.fill()
            }
        }
    }
}
