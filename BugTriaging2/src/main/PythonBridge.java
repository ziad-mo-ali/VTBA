package main;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import utils.Constants;

public class PythonBridge {
	private static final String PYTHON_SCRIPT = Constants.SIM_BRIDGE_SCRIPT;
	private static final int READY_TIMEOUT_SECONDS = 60;
	
	private static PythonBridge instance = null;
	
	private Process process = null;
	private BufferedWriter stdin = null;
	private BufferedReader stdout = null;
	
	/**
	 * Private constructor. Starts the Python process and waits for READY signal.
	 */
	private PythonBridge() throws RuntimeException {
		try {
			ProcessBuilder pb = new ProcessBuilder("python3", PYTHON_SCRIPT);
			pb.directory(new File("/content/VTBA/"));
			this.process = pb.start();
			
			this.stdin = new BufferedWriter(
				new OutputStreamWriter(process.getOutputStream(), StandardCharsets.UTF_8));
			this.stdout = new BufferedReader(
				new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8));
			
			// Wait for READY signal with timeout
			long startTime = System.currentTimeMillis();
			String line;
			while ((line = stdout.readLine()) != null) {
				line = line.trim();
				if (line.equals("READY")) {
					// Process is ready
					registerShutdownHook();
					return;
				}
				
				// Check timeout
				long elapsedSeconds = (System.currentTimeMillis() - startTime) / 1000;
				if (elapsedSeconds > READY_TIMEOUT_SECONDS) {
					throw new RuntimeException("Python bridge process did not send READY within " 
						+ READY_TIMEOUT_SECONDS + " seconds");
				}
			}
			
			throw new RuntimeException("Python bridge process ended without sending READY");
			
		} catch (IOException ioe) {
			throw new RuntimeException("Failed to start Python bridge process", ioe);
		}
	}
	
	/**
	 * Lazy singleton accessor. Thread-safe.
	 */
	public static synchronized PythonBridge getInstance() {
		if (instance == null) {
			instance = new PythonBridge();
		}
		return instance;
	}
	
	/**
	 * Register shutdown hook to cleanly terminate Python process on JVM exit.
	 */
	private void registerShutdownHook() {
		Runtime.getRuntime().addShutdownHook(new Thread(() -> {
			PythonBridge.this.shutdown();
		}));
	}
	
	/**
	 * Get token-tag similarities from Python Word2Vec bridge.
	 * Returns empty map if tokens or tags are empty.
	 * Thread-safe.
	 */
	public synchronized Map<String, Double> getSimilarities(List<String> tokens, List<String> tags) {
		if (tokens == null || tokens.isEmpty() || tags == null || tags.isEmpty()) {
			return new HashMap<>();
		}
		
		try {
			// Build JSON request using json-simple
			JSONObject request = new JSONObject();
			JSONArray tokArr = new JSONArray();
			tokArr.addAll(tokens);
			JSONArray tagArr = new JSONArray();
			tagArr.addAll(tags);
			request.put("tokens", tokArr);
			request.put("tags", tagArr);
			
			// Send request
			String jsonString = request.toJSONString();
			stdin.write(jsonString);
			stdin.write("\n");
			stdin.flush();
			
			// Read response
			String responseLine = stdout.readLine();
			if (responseLine == null) {
				return new HashMap<>();
			}
			
			responseLine = responseLine.trim();
			if (responseLine.isEmpty()) {
				return new HashMap<>();
			}
			
			// Parse response JSON
			JSONParser parser = new JSONParser();
			Object obj = parser.parse(responseLine);
			
			if (!(obj instanceof JSONObject)) {
				return new HashMap<>();
			}
			
			JSONObject responseJson = (JSONObject) obj;
			
			// Check for error
			if (responseJson.containsKey("error")) {
				System.err.println("Python bridge error: " + responseJson.get("error"));
				return new HashMap<>();
			}
			
			// Extract similarities
			Map<String, Double> similarities = new HashMap<>();
			for (Object key : responseJson.keySet()) {
				String keyStr = (String) key;
				Object val = responseJson.get(keyStr);
				if (val instanceof Number) {
					similarities.put(keyStr, ((Number) val).doubleValue());
				}
			}
			
			return similarities;
			
		} catch (ParseException pe) {
			System.err.println("Failed to parse Python bridge response: " + pe.getMessage());
			pe.printStackTrace();
			return new HashMap<>();
		} catch (IOException ioe) {
			System.err.println("IO error communicating with Python bridge: " + ioe.getMessage());
			ioe.printStackTrace();
			return new HashMap<>();
		}
	}
	
	/**
	 * Gracefully shutdown the Python process.
	 */
	public void shutdown() {
		if (process == null) {
			return;
		}
		
		try {
			// Send EXIT command
			if (stdin != null) {
				stdin.write("EXIT\n");
				stdin.flush();
			}
			
			// Wait up to 5 seconds for process to terminate
			if (!process.waitFor(5, TimeUnit.SECONDS)) {
				process.destroyForcibly();
			}
		} catch (IOException ioe) {
			System.err.println("Error sending EXIT to Python bridge: " + ioe.getMessage());
			process.destroyForcibly();
		} catch (InterruptedException ie) {
			Thread.currentThread().interrupt();
			process.destroyForcibly();
		}
	}
}
