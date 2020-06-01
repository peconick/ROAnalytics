import pandas
class cashflow_options():
    
    def __init__(self, input_file_name,interest_rate=0):
        self.network=pandas.read_csv(input_file_name)
        self.max_period= int(self.network[['period']].max().array[0])
        self.interest_rate = interest_rate
        self.set_interest_rate()
        self.get_nodes()
        self.add_network_label()
        
    def add_network_label(self):
        nodes = self.nodes
        df = pandas.merge(self.network, nodes,  how='left', left_on=['period','org_node'], right_on = ['period','node'])
        df = df.rename(columns={"label": "org_node_label"})
        del df['node']
        nodes['period']=nodes['period']-1
        df = pandas.merge(df, nodes,  how='left', left_on=['period','dest_node'], right_on = ['period','node'])
        df = df.rename(columns={"label": "dest_node_label"})
        del df['node']
        self.network = df
       
    def get_nodes(self):
        self.nodes = self.network[['period','org_node']].drop_duplicates()
        self.nodes.columns = ['period','node']

        # Identify the number of nodes on end period and append to nodes
        is_max_period = self.network['period']==self.max_period
        end_period_nodes= self.network[is_max_period][['dest_node']].drop_duplicates()
        end_period_nodes['period']=self.max_period+1
        end_period_nodes.columns =['node','period']
        self.nodes = self.nodes.append(end_period_nodes)
        
        #Add Alphabetical labels
        n_nodes=len(self.nodes)
        A=ord('A')
        labels = [chr(i) for i in range(A,A+n_nodes)]
        self.nodes['label'] = labels
        
    def set_interest_rate(self):
        self.network['adjusted_cashflow'] = self.network['cashflow']/(
            (1+self.interest_rate)**(self.network['period']+1))

    def NPV_max(self):
        # Build initial solutions
        grouped_network = self.network.groupby('period')
        current_solution =  grouped_network.get_group(0)[['adjusted_cashflow','org_node_label','dest_node_label']]
        current_solution.columns=['NPV','node_0','node_1']
        
        # Advance to next period
        for period in range(1,self.max_period+1):
            # Manage column names
            match_node=f'node_{period}'
            period_node=f'node_{period+1}'
            
            # Select top solution per node (branch and bound)            
            current_solution = self.filter_best_solutions(current_solution)

            # Accumulate period cashflow
            period_cashflows = grouped_network.get_group(period)[['adjusted_cashflow','org_node_label','dest_node_label']]
            current_solution= pandas.merge(current_solution, period_cashflows,  how='left', left_on=[match_node], right_on = ['org_node_label'])
            current_solution['NPV']=current_solution['NPV']+current_solution['adjusted_cashflow']
            
            # Rename Columns
            del current_solution['org_node_label']
            del current_solution['adjusted_cashflow']
            current_solution = current_solution.rename(columns={"dest_node_label":period_node})
        current_solution = self.get_max_rows(current_solution,'NPV')
        return(current_solution)
        
    def filter_best_solutions(self,solutions):
        # Build Filter params
        columns = solutions.columns
        ncols = len(columns)
        group_column = list(columns)[ncols-1]
        # Filter best node resuls index
        best_solutions=self.get_max_rows(solutions,'NPV',group_column)
        return(best_solutions)
    
    def NPV_greedy(self):
        # Filter only maximum cashflow values for each node
        filtered_network = self.get_max_rows(self.network,'adjusted_cashflow','org_node_label')
        grouped_network = filtered_network.groupby('period')

        # Build initial solutions
        current_solution = grouped_network.get_group(0)
        current_solution = current_solution[['adjusted_cashflow','org_node_label','dest_node_label']]
        current_solution.columns=['NPV','node_0','node_1']
        current_node = str(current_solution.iloc[0]['node_1'])
        
        # Advance to next Period
        for period in range(1,self.max_period+1):
            period_node=f'node_{period+1}'
            #Filter period nodes based on last period greedy option
            period_nodes = grouped_network.get_group(period)
            idx=period_nodes['org_node_label']==current_node
            greedy_option = period_nodes[idx]

            period_cashflow = greedy_option.iloc[0]['adjusted_cashflow']
            next_node = greedy_option.iloc[0]['dest_node_label']
            
            current_solution[period_node] = next_node
            current_solution['NPV'] = current_solution['NPV'] + period_cashflow
            current_node = next_node
        current_solution = self.get_max_rows(current_solution,'NPV')
        return (current_solution)

    def get_max_rows(self,data_frame,value_var,group_var=None):
        # Filters a data frame where the value_var is maximum
        if (group_var!=None): # max by group
            idx = data_frame.groupby(group_var)[value_var].transform(max) == data_frame[value_var]
        else: # gobal max
            idx = data_frame[value_var] == data_frame[value_var].max()

        return(data_frame[idx])


if __name__ == '__main__':
    
    cashflow_opt=cashflow_options('example_flow_network.dat',0.1)
    NPV_greedy_solutions = cashflow_opt.NPV_greedy()
    print('\nGreedy Solution')
    print(NPV_greedy_solutions)
    NPV_max_solutions = cashflow_opt.NPV_max()
    print('\nMax NPV Solution')
    print(NPV_max_solutions)
    

    
    
          
