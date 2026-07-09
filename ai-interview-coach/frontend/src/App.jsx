import { Routes, Route } from "react-router-dom";
import UploadScreen from "./pages/UploadScreen.jsx";
import InterviewScreen from "./pages/InterviewScreen.jsx";
import ReportScreen from "./pages/ReportScreen.jsx";
import HistoryScreen from "./pages/HistoryScreen.jsx";
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadScreen />} />
      <Route path="/interview/:sessionId" element={<InterviewScreen />} />
      <Route path="/report/:sessionId" element={<ReportScreen />} />
      <Route path="/history" element={<HistoryScreen />} />
    </Routes>
  );
}
