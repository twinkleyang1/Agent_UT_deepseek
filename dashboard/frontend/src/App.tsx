import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ProjectList from "./pages/ProjectList";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ProjectList />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
