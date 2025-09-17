// Simple time-based greetings

const morningGreetings = [
  "Good morning!",
  "Morning!",
  "Good morning! How are you?",
  "Morning! How's it going?",
  "Good morning! How are you doing?",
  "Morning! How are you?",
  "Good morning! How's your day?",
  "Morning! How are you doing today?",
  "Buenos días!",
  "Good morning! How are you feeling?"
];

const afternoonGreetings = [
  "Good afternoon!",
  "Afternoon!",
  "Good afternoon! How are you?",
  "Afternoon! How's it going?",
  "Good afternoon! How are you doing?",
  "Afternoon! How are you?",
  "Good afternoon! How's your day?",
  "Afternoon! How are you doing?",
  "Buenas tardes!",
  "Good afternoon! How are you feeling?"
];

const eveningGreetings = [
  "Good evening!",
  "Evening!",
  "Good evening! How are you?",
  "Evening! How's it going?",
  "Good evening! How are you doing?",
  "Evening! How are you?",
  "Good evening! How was your day?",
  "Evening! How are you doing?",
  "Buenas noches!",
  "Good evening! How are you feeling?"
];

const nightGreetings = [
  "Good evening!",
  "Evening!",
  "Good evening! How are you?",
  "Evening! How's it going?",
  "Good evening! How are you doing?",
  "Evening! How are you?",
  "Good evening! How was your day?",
  "Evening! How are you doing?",
  "Buenas noches!",
  "Good evening! How are you feeling?"
];

/**
 * Returns a simple, time-based greeting.
 * @returns {string} The greeting string.
 */
export const getTimeBasedGreeting = (): string => {
  const hour = new Date().getHours();
  
  // Morning (5 AM - 11 AM)
  if (hour >= 5 && hour < 12) {
    return morningGreetings[Math.floor(Math.random() * morningGreetings.length)];
  }
  
  // Afternoon (12 PM - 5 PM)
  if (hour >= 12 && hour < 17) {
    return afternoonGreetings[Math.floor(Math.random() * afternoonGreetings.length)];
  }
  
  // Evening (5 PM - 11 PM)
  if (hour >= 17 && hour < 23) {
    return eveningGreetings[Math.floor(Math.random() * eveningGreetings.length)];
  }
  
  // Night (11 PM - 5 AM)
  return nightGreetings[Math.floor(Math.random() * nightGreetings.length)];
};
