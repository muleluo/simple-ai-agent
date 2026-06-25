import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 800
    visible: true
    title: "AI 桌面助手"

    // 全局配色方案（无 emoji）
    property color primaryColor: "#2563eb"      // 主色调（蓝）
    property color surfaceColor: "#ffffff"       // 表面白色
    property color backgroundColor: "#f8fafc"    // 背景浅灰
    property color borderColor: "#e2e8f0"        // 边框颜色
    property color textPrimary: "#1e293b"        // 主文字
    property color textSecondary: "#64748b"      // 次要文字
    property color hoverColor: "#f1f5f9"         // 悬停背景
    property color selectedColor: "#dbeafe"      // 选中背景

    // 动画时长
    property int animationDuration: 200
    property int slowAnimationDuration: 300

    // 阴影参数
    property real shadowOpacity: 0.1

    color: backgroundColor

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        // 左侧边栏
        Rectangle {
            id: sidebar
            SplitView.preferredWidth: 280
            SplitView.minimumWidth: 200
            SplitView.maximumWidth: 400
            color: surfaceColor

            // 右侧边框
            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: borderColor
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 16

                // 标题
                Text {
                    text: "对话历史"
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    color: textPrimary
                    Layout.fillWidth: true
                }

                // 新建对话按钮
                Button {
                    id: newChatButton
                    Layout.fillWidth: true
                    Layout.preferredHeight: 44

                    property bool isHovered: false

                    HoverHandler {
                        onHoveredChanged: newChatButton.isHovered = hovered
                    }

                    background: Rectangle {
                        color: newChatButton.pressed ? "#1d4ed8" : primaryColor
                        radius: 8

                        Behavior on color {
                            ColorAnimation { duration: animationDuration }
                        }

                        // 按钮阴影
                        layer.enabled: true
                        layer.effect: DropShadow {
                            horizontalOffset: 0
                            verticalOffset: 2
                            radius: 12
                            samples: 17
                            color: "#20000000"
                            transparentBorder: true
                        }

                        // 悬停光效
                        Rectangle {
                            anchors.fill: parent
                            radius: parent.radius
                            color: "#ffffff"
                            opacity: newChatButton.isHovered ? 0.15 : 0

                            Behavior on opacity {
                                NumberAnimation { duration: animationDuration }
                            }
                        }

                        // 按压弹性效果
                        scale: newChatButton.pressed ? 0.95 : 1.0
                        Behavior on scale {
                            NumberAnimation {
                                duration: 100
                                easing.type: Easing.OutBack
                            }
                        }
                    }

                    contentItem: Text {
                        text: "+ 新建对话"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        pyBridge.createNewChat()
                    }
                }

                // 会话列表
                ListView {
                    id: sessionListView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 8

                    model: sessionListModel

                    delegate: ItemDelegate {
                        width: sessionListView.width
                        height: 60

                        property bool isHovered: false

                        HoverHandler {
                            onHoveredChanged: isHovered = hovered
                        }

                        background: Rectangle {
                            color: {
                                if (model.isSelected) return selectedColor
                                if (isHovered) return hoverColor
                                return "transparent"
                            }
                            radius: 8

                            // 选中指示器
                            Rectangle {
                                visible: model.isSelected
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                width: 3
                                height: parent.height * 0.6
                                radius: 2
                                color: primaryColor
                            }

                            Behavior on color {
                                ColorAnimation { duration: animationDuration }
                            }
                        }

                        contentItem: ColumnLayout {
                            spacing: 4
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            anchors.verticalCenter: parent.verticalCenter

                            Text {
                                text: model.title
                                font.pixelSize: 14
                                font.weight: model.isSelected ? Font.Medium : Font.Normal
                                color: textPrimary
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Text {
                                text: model.timestamp
                                font.pixelSize: 12
                                color: textSecondary
                                Layout.fillWidth: true
                            }
                        }

                        onClicked: {
                            pyBridge.switchSession(model.sessionId)
                        }

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.RightButton
                            onClicked: {
                                sessionContextMenu.currentSessionId = model.sessionId
                                sessionContextMenu.popup()
                            }
                        }
                    }

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                        contentItem: Rectangle {
                            implicitWidth: 6
                            radius: 3
                            color: textSecondary
                            opacity: 0.3
                        }
                    }
                }
            }
        }

        // 右侧聊天区域
        Rectangle {
            id: chatArea
            SplitView.fillWidth: true
            color: backgroundColor

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                // 顶部标题栏
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    color: surfaceColor
                    radius: 12

                    layer.enabled: true
                    layer.effect: DropShadow {
                        horizontalOffset: 0
                        verticalOffset: 1
                        radius: 8
                        samples: 17
                        color: "#1A000000"
                        transparentBorder: true
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12

                        Text {
                            text: "和 AI 聊天"
                            font.pixelSize: 20
                            font.weight: Font.DemiBold
                            color: textPrimary
                            Layout.fillWidth: true
                        }

                        Button {
                            id: settingsButton
                            Layout.preferredWidth: 36
                            Layout.preferredHeight: 36

                            property bool isHovered: false

                            HoverHandler {
                                onHoveredChanged: settingsButton.isHovered = hovered
                            }

                            background: Rectangle {
                                color: settingsButton.isHovered ? hoverColor : "transparent"
                                radius: 6
                                Behavior on color {
                                    ColorAnimation { duration: animationDuration }
                                }
                            }

                            contentItem: Text {
                                text: "···"
                                font.pixelSize: 20
                                font.weight: Font.Bold
                                color: textSecondary
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }

                            onClicked: {
                                settingsMenu.popup()
                            }
                        }
                    }
                }

                // 消息显示区域
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: surfaceColor
                    radius: 12

                    layer.enabled: true
                    layer.effect: DropShadow {
                        horizontalOffset: 0
                        verticalOffset: 1
                        radius: 8
                        samples: 17
                        color: "#1A000000"
                        transparentBorder: true
                    }

                    ListView {
                        id: messageListView
                        anchors.fill: parent
                        anchors.margins: 16
                        clip: true
                        spacing: 16
                        model: messageListModel

                        delegate: MessageBubble {
                            width: messageListView.width
                            messageData: model
                        }

                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                            contentItem: Rectangle {
                                implicitWidth: 6
                                radius: 3
                                color: textSecondary
                                opacity: 0.3
                            }
                        }

                        onCountChanged: {
                            positionViewAtEnd()
                        }
                    }
                }

                // 输入区域
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 120
                    color: surfaceColor
                    radius: 12

                    layer.enabled: true
                    layer.effect: DropShadow {
                        horizontalOffset: 0
                        verticalOffset: 1
                        radius: 8
                        samples: 17
                        color: "#1A000000"
                        transparentBorder: true
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true

                            TextArea {
                                id: inputArea
                                placeholderText: "在这里输入消息..."
                                font.pixelSize: 14
                                color: textPrimary
                                wrapMode: TextArea.Wrap
                                selectByMouse: true

                                background: Rectangle {
                                    color: inputArea.focus ? hoverColor : "transparent"
                                    radius: 6
                                    border.width: inputArea.focus ? 2 : 0
                                    border.color: primaryColor
                                    Behavior on color {
                                        ColorAnimation { duration: animationDuration }
                                    }
                                }

                                Keys.onReturnPressed: {
                                    if (event.modifiers & Qt.ControlModifier) {
                                        sendButton.clicked()
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Button {
                                id: attachButton
                                text: "附加文件"
                                Layout.preferredHeight: 36

                                property bool isHovered: false

                                HoverHandler {
                                    onHoveredChanged: attachButton.isHovered = hovered
                                }

                                background: Rectangle {
                                    color: attachButton.isHovered ? hoverColor : "transparent"
                                    radius: 6
                                    border.width: 1
                                    border.color: borderColor
                                    Behavior on color {
                                        ColorAnimation { duration: animationDuration }
                                    }
                                }
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 13
                                    color: textSecondary
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                onClicked: { pyBridge.attachFile() }
                            }

                            Button {
                                id: reminderButton
                                text: "提醒"
                                Layout.preferredHeight: 36

                                property bool isHovered: false

                                HoverHandler {
                                    onHoveredChanged: reminderButton.isHovered = hovered
                                }

                                background: Rectangle {
                                    color: reminderButton.isHovered ? hoverColor : "transparent"
                                    radius: 6
                                    border.width: 1
                                    border.color: borderColor
                                    Behavior on color {
                                        ColorAnimation { duration: animationDuration }
                                    }
                                }
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 13
                                    color: textSecondary
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                onClicked: { pyBridge.showReminderDialog() }
                            }

                            Item { Layout.fillWidth: true }

                            Button {
                                id: clearButton
                                text: "清空"
                                Layout.preferredHeight: 36

                                property bool isHovered: false

                                HoverHandler {
                                    onHoveredChanged: clearButton.isHovered = hovered
                                }

                                background: Rectangle {
                                    color: clearButton.isHovered ? "#fee2e2" : "transparent"
                                    radius: 6
                                    border.width: 1
                                    border.color: "#fecaca"
                                    Behavior on color {
                                        ColorAnimation { duration: animationDuration }
                                    }
                                }
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 13
                                    color: "#dc2626"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                onClicked: { pyBridge.clearCurrentChat() }
                            }

                            Button {
                                id: sendButton
                                text: "发送"
                                Layout.preferredHeight: 36
                                Layout.preferredWidth: 80
                                enabled: inputArea.text.trim().length > 0

                                property bool isHovered: false

                                HoverHandler {
                                    onHoveredChanged: sendButton.isHovered = hovered
                                }

                                background: Rectangle {
                                    color: {
                                        if (!sendButton.enabled) return borderColor
                                        if (sendButton.pressed) return "#1d4ed8"
                                        return primaryColor
                                    }
                                    radius: 6

                                    Behavior on color {
                                        ColorAnimation { duration: animationDuration }
                                    }

                                    layer.enabled: sendButton.enabled
                                    layer.effect: DropShadow {
                                        horizontalOffset: 0
                                        verticalOffset: 2
                                        radius: sendButton.isHovered ? 16 : 12
                                        samples: 17
                                        color: sendButton.isHovered ? "#4D2563eb" : "#262563eb"
                                        transparentBorder: true
                                    }

                                    scale: sendButton.pressed ? 0.95 : 1.0
                                    Behavior on scale {
                                        NumberAnimation {
                                            duration: 100
                                            easing.type: Easing.OutBack
                                        }
                                    }
                                }

                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 14
                                    font.weight: Font.Medium
                                    color: sendButton.enabled ? "white" : textSecondary
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                onClicked: {
                                    if (inputArea.text.trim().length > 0) {
                                        pyBridge.sendMessage(inputArea.text)
                                        inputArea.text = ""
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Menu {
        id: sessionContextMenu
        property string currentSessionId: ""
        MenuItem {
            text: "重命名"
            onTriggered: { pyBridge.renameSession(sessionContextMenu.currentSessionId) }
        }
        MenuItem {
            text: "删除"
            onTriggered: { pyBridge.deleteSession(sessionContextMenu.currentSessionId) }
        }
    }

    Menu {
        id: settingsMenu
        MenuItem {
            text: "上传到知识库"
            onTriggered: { pyBridge.uploadToKnowledgeBase() }
        }
        MenuItem {
            id: webSearchMenuItem
            checkable: true
            text: "联网搜索"
            checked: false
            onTriggered: { pyBridge.toggleWebSearch() }
        }
    }
}
