import { OverviewProvider, RosProvider } from "../contexts";

type ProviderProps = {
  children: React.ReactNode;
};

const Provider: React.FC<ProviderProps> = ({ children }) => (
  <RosProvider>
    <OverviewProvider>{children}</OverviewProvider>
  </RosProvider>
);

export default Provider;
