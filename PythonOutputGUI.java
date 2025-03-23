import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionListener;
import java.io.*;
import java.util.HashMap;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

public class PythonOutputGUI {
    private JTextArea textArea;
    private Process process;
    private JButton startButton, pauseButton;
    private JButton sendButton, startAudioButton, stopButton;
    private boolean isPaused = false;
    private BufferedWriter pythonWriter;
    private BufferedReader pythonReader;
    private JTextField inputField;
    private boolean conversationRunning = false;
    private String selectedLanguage = "English"; // Default language
    private HashMap<String, String> cultureProfiles;
    private Thread stdoutThread;
    private Thread stderrThread;


    public PythonOutputGUI() {
        initializeLanguageToNameMap();
        showInitGUI();
    }

    private void initializeLanguageToNameMap() {
        // We could read this from the .json file but then you need Maven to build the project with Gson dependency
        // Im not assuming that we all have this so I hardcoded the values
        cultureProfiles = new HashMap<>();
        cultureProfiles.put("American", "Aria");
        cultureProfiles.put("French", "Sophie");
        cultureProfiles.put("Spanish", "Elena");
        cultureProfiles.put("German", "Hannah");
        cultureProfiles.put("Japanese", "Hana");
    }

    private void showInitGUI() { // language selection frame
        JFrame languageFrame = new JFrame("PenPal GUI");
        languageFrame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        languageFrame.setSize(400, 200);
        languageFrame.setLayout(new BorderLayout());

        String[] languages = {"French", "Spanish", "German", "Japanese"}; // no english
        JComboBox<String> languageDropdown = new JComboBox<>(languages);

        JButton startButton = new JButton("Start");

        startButton.addActionListener(e -> {
            selectedLanguage = (String) languageDropdown.getSelectedItem(); 
            languageFrame.dispose();
            startMainGUI();
        });

        JPanel panel = new JPanel();
        panel.add(new JLabel("Select a language:"));
        panel.add(languageDropdown);
        panel.add(startButton);

        languageFrame.add(panel, BorderLayout.CENTER);
        languageFrame.setLocationRelativeTo(null);
        languageFrame.setVisible(true);
    }

    private void startMainGUI() {
        // Create main frame
        JFrame frame = new JFrame("PenPal GUI");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(800, 600);
        frame.setLayout(new BorderLayout());

        // Left panel
        JPanel leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setPreferredSize(new Dimension(200, 400));
        
        JLabel nameLabel = new JLabel("Name: " + cultureProfiles.get(this.selectedLanguage)); 
        JLabel languageLabel = new JLabel("Language: " + this.selectedLanguage); 
        startButton = new JButton("Start Conversation");
        pauseButton = new JButton("Pause Conversation");
        stopButton = new JButton("Stop Conversation");
        startAudioButton = new JButton("Start Audio Input");

        leftPanel.add(nameLabel);
        leftPanel.add(languageLabel);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 10)));
        leftPanel.add(startButton);
        leftPanel.add(pauseButton);
        leftPanel.add(stopButton);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 10)));
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

        frame.add(leftPanel, BorderLayout.WEST);
        frame.add(scrollPane, BorderLayout.CENTER);
        frame.add(inputPanel, BorderLayout.SOUTH);

        // Button actions
        startButton.addActionListener(e -> startPythonScript());
        pauseButton.addActionListener(e -> togglePauseResume());
        stopButton.addActionListener(e -> stopPythonScript());
        sendButton.addActionListener(e -> sendTextInputToPython());
        startAudioButton.addActionListener(e -> sendToPython("START_AUDIO"));

        frame.addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                stopPythonScript();
            }
        });
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }

    private void startPythonScript() {
        if (conversationRunning) {
            textArea.append("Conversation already running. Button is disabled. Please stop the current conversation first.\n");
            return;
        }

        textArea.setText("");

        try {
            ProcessBuilder pb = new ProcessBuilder("python", "-u", "penpal.py", this.selectedLanguage, this.cultureProfiles.get(this.selectedLanguage)); // Ensure unbuffered output
            // pb.redirectErrorStream(true); // Merge stderr with stdout
            process = pb.start();
            System.out.println("Process started with PID: " + process.pid());
            conversationRunning = true;

            pythonReader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            pythonWriter = new BufferedWriter(new OutputStreamWriter(process.getOutputStream()));
            BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()));

            // Read output in a separate thread
            stdoutThread = new Thread(() -> {
                String line;
                try {
                    while ((line = pythonReader.readLine()) != null) {
                        String finalLine = line;
                        System.out.println("Python Output: " + line); // Debug output
                        SwingUtilities.invokeLater(() -> textArea.append(finalLine + "\n")); // Ensure safe UI updates
                    }
                } catch (Exception ex) {
                    if (conversationRunning) {
                        System.err.println("Error: Unable to read from Python process. The stream may be closed.");
                    }
                }
            });
            stdoutThread.start();

            // Read stderr in a separate thread and print to the terminal
            stderrThread = new Thread(() -> {
                String line;
                try {
                    while ((line = errorReader.readLine()) != null) {
                        System.err.println("Python Error: " + line); // Print stderr to the terminal
                    }
                } catch (Exception ex) {
                    System.err.println("Error: Unable to read from Python process stderr. The stream may be closed.");
                }
            });
            stderrThread.start();

        } catch (Exception e) {
            System.err.println("Error: Unable to start Python process.");
        }
    }

    private void sendToPython(String message) {
        try {
            if (pythonWriter != null) {
                pythonWriter.write(message + "\n");
                pythonWriter.flush();
            }
        } catch (IOException e) {
            System.err.println("Error: Unable to send message to Python process. The stream may be closed.");
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
                System.err.println("Error: Unable to send user input to Python process. The stream may be closed.");
            }
        }
    }

    private void togglePauseResume() {
        if (process != null) {
            try {
                if (isPaused) {
                    Runtime.getRuntime().exec(new String[] { "sh", "-c", "kill -CONT " + process.pid() });
                    pauseButton.setText("Pause Conversation");
                } else {
                    Runtime.getRuntime().exec(new String[] { "sh", "-c", "kill -STOP " + process.pid() });
                    pauseButton.setText("Resume Conversation");
                }
                isPaused = !isPaused;
            } catch (Exception e) {
            }
        }
    }

    private void stopPythonScript() {
        if (process != null) {
            try {
                // Send the EXIT command to the Python script
                if (pythonWriter != null) {
                    sendToPython("EXIT");
                    pythonWriter.close(); // Close the writer
                    System.out.println("Writer closed\n");
                }

                // Wait for the process to terminate
                process.waitFor();

            } catch (IOException e) {
                System.err.println("Error: Unable to close the writer or send the EXIT command.");
            } catch (InterruptedException e) {
                System.err.println("Error: Interrupted while waiting for the Python process to terminate.");
            } finally {
                // Destroy the process if it hasn't terminated
                if (process.isAlive()) {
                    process.destroy();
                }
            
             // Interrupt and join the threads
            if (stdoutThread != null && stdoutThread.isAlive()) {
                stdoutThread.interrupt();
                try {
                    stdoutThread.join(); // Wait for the thread to finish
                } catch (InterruptedException e) {
                    System.err.println("Error: Interrupted while waiting for stdout thread to finish.");
                }
            }

            if (stderrThread != null && stderrThread.isAlive()) {
                stderrThread.interrupt();
                try {
                    stderrThread.join(); // Wait for the thread to finish
                } catch (InterruptedException e) {
                    System.err.println("Error: Interrupted while waiting for stderr thread to finish.");
                }
            }

                // Close the reader and process streams
                try {
                    if (pythonReader != null) {
                        pythonReader.close(); // Close the reader
                        System.out.println("Reader closed\n");
                    }
                    if (process.getInputStream() != null) {
                        process.getInputStream().close();
                    }
                    if (process.getErrorStream() != null) {
                        process.getErrorStream().close();
                    }
                    if (process.getOutputStream() != null) {
                        process.getOutputStream().close();
                    }
                } catch (IOException e) {
                    System.err.println("Error: Unable to close process streams.");
                }

                textArea.append("\nConversation Ended\n");
            }
        }
        conversationRunning = false;
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(PythonOutputGUI::new);
    }
}
