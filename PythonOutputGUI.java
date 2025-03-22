import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionListener;
import java.io.*;

public class PythonOutputGUI {
    private JTextArea textArea;
    private Process process;
    private JButton startButton, pauseButton;
    private JButton sendButton, startAudioButton, stopButton;
    private boolean isPaused = false;
    private BufferedWriter pythonWriter;
    private JTextField inputField;

    public PythonOutputGUI() {
        // Create main frame
        JFrame frame = new JFrame("PenPal GUI");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(600, 400);
        frame.setLayout(new BorderLayout());

        // Left panel
        JPanel leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setPreferredSize(new Dimension(200, 400));

        JLabel nameLabel = new JLabel("Name: User"); // add the CA name here
        JLabel languageLabel = new JLabel("Language: English"); // same here for language
        startButton = new JButton("Start Conversation");
        pauseButton = new JButton("Pause Conversation");
        stopButton = new JButton("Stop Conversation");
        startAudioButton = new JButton("Start Audio Input");

        leftPanel.add(nameLabel);
        leftPanel.add(languageLabel);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 10))); // Spacer
        leftPanel.add(startButton);
        leftPanel.add(pauseButton);
        leftPanel.add(stopButton);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 10))); // Spacer
        leftPanel.add(startAudioButton);

        // Right panel (Output area)
        textArea = new JTextArea(20, 30);
        textArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(textArea);

        // Bottom Panel for user input
        JPanel inputPanel = new JPanel();
        inputPanel.setLayout(new BorderLayout());

        inputField = new JTextField();
        sendButton = new JButton("Send");

        inputPanel.add(inputField, BorderLayout.CENTER);
        inputPanel.add(sendButton, BorderLayout.EAST);

        // Add panels to frame
        frame.add(leftPanel, BorderLayout.WEST);
        frame.add(scrollPane, BorderLayout.CENTER);
        frame.add(inputPanel, BorderLayout.SOUTH);

        // Button actions
        startButton.addActionListener(e -> startPythonScript());
        pauseButton.addActionListener(e -> togglePauseResume());
        // stopButton.addActionListener(e -> stopPythonScript());
        stopButton.addActionListener(e -> sendToPython("EXIT"));
        sendButton.addActionListener(e -> sendTextInputToPython());
        startAudioButton.addActionListener(e -> sendToPython("START_AUDIO"));


        frame.setVisible(true);
    }

    // private void startPythonScript() {
    //     try {
    //         ProcessBuilder pb = new ProcessBuilder("python3", "-u", "CA/penpal-ca/penpal.py");
    //         process = pb.start();

    //         BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
    //         pythonWriter = new BufferedWriter(new OutputStreamWriter(process.getOutputStream()));

    //         new Thread(() -> {
    //             String line;
    //             try {
    //                 while ((line = reader.readLine()) != null) {
    //                     textArea.append(line + "\n");
    //                 }
    //             } catch (Exception ex) {
    //                 ex.printStackTrace();
    //             }
    //         }).start();
    //     } catch (Exception e) {
    //         e.printStackTrace();
    //     }
    // }

    private void startPythonScript() {
        try {
            ProcessBuilder pb = new ProcessBuilder("python3", "-u", "penpal.py"); // Ensure unbuffered output
            pb.redirectErrorStream(true);  // Merge stderr with stdout
            process = pb.start();
            System.out.println("Process started with PID: " + process.pid());
    
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            pythonWriter = new BufferedWriter(new OutputStreamWriter(process.getOutputStream()));
    
            // Read output in a separate thread
            new Thread(() -> {
                String line;
                try {
                    while ((line = reader.readLine()) != null) {
                        String finalLine = line;
                        System.out.println("Python Output: " + line); // Debug output
                        SwingUtilities.invokeLater(() -> textArea.append(finalLine + "\n")); // Ensure safe UI updates
                    }
                } catch (Exception ex) {
                    ex.printStackTrace();
                }
            }).start();
    
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    

    private void sendToPython(String message) {
        try {
            if (pythonWriter != null) {
                pythonWriter.write(message + "\n");
                pythonWriter.flush();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void sendTextInputToPython() {
        if (process != null && pythonWriter != null) {
            try {
                String userInput = inputField.getText().trim();
                if (!userInput.isEmpty()) {
                    pythonWriter.write(userInput + "\n");
                    pythonWriter.flush();
                    inputField.setText(""); // Clear input field after sending
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private void togglePauseResume() {
        if (process != null) {
            try {
                if (isPaused) {
                    Runtime.getRuntime().exec(new String[]{"sh", "-c", "kill -CONT " + process.pid()});
                    pauseButton.setText("Pause Conversation");
                } else {
                    Runtime.getRuntime().exec(new String[]{"sh", "-c", "kill -STOP " + process.pid()});
                    pauseButton.setText("Resume Conversation");
                }
                isPaused = !isPaused;
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private void stopPythonScript() {
        if (process != null) {
            process.destroy();
            textArea.append("\n Conversation Ended\n");
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(PythonOutputGUI::new);
    }
}
