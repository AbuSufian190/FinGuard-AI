import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import About from "./pages/About";
import BatchDetection from "./pages/BatchDetection";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import ModelInformation from "./pages/ModelInformation";
import ModelPerformance from "./pages/ModelPerformance";
import TransactionAnalysis from "./pages/TransactionAnalysis";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="analyze" element={<TransactionAnalysis />} />
          <Route path="batch" element={<BatchDetection />} />
          <Route path="performance" element={<ModelPerformance />} />
          <Route path="history" element={<History />} />
          <Route path="model" element={<ModelInformation />} />
          <Route path="about" element={<About />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
