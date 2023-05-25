import { OverviewProvider, RosProvider } from "../contexts";

const Provider: React.FC = ({ children }) => (
  <RosProvider>
    <OverviewProvider>{children}</OverviewProvider>
  </RosProvider>
);

export default Provider;
