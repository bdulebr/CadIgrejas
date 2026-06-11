import React from 'react';
import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import LoginScreen from './src/screens/LoginScreen';
import HomeScreen from './src/screens/HomeScreen';
import EscalaDepartamentoScreen from './src/screens/EscalaDepartamentoScreen';
import AusenciasScreen from './src/screens/AusenciasScreen';

// Leader Screens
import LiderScreen from './src/screens/LiderScreen';
import LiderMembrosScreen from './src/screens/LiderMembrosScreen';
import CompetenciasScreen from './src/screens/CompetenciasScreen';
import EditorEscalaScreen from './src/screens/EditorEscalaScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();
const LiderStack = createNativeStackNavigator();

function LiderStackNavigator() {
  return (
    <LiderStack.Navigator screenOptions={{
      headerStyle: { backgroundColor: '#1f2937' },
      headerTintColor: '#fff',
    }}>
      <LiderStack.Screen name="LiderDashboard" component={LiderScreen} options={{ headerShown: false }} />
      <LiderStack.Screen name="LiderMembros" component={LiderMembrosScreen} options={{ title: 'Membros' }} />
      <LiderStack.Screen name="Competencias" component={CompetenciasScreen} options={{ title: 'Meses de Escala' }} />
      <LiderStack.Screen name="EditorEscala" component={EditorEscalaScreen} options={{ title: 'Editor Manual' }} />
    </LiderStack.Navigator>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;
          if (route.name === 'Minha Escala') iconName = focused ? 'person' : 'person-outline';
          else if (route.name === 'Depto (Geral)') iconName = focused ? 'people' : 'people-outline';
          else if (route.name === 'Ausências') iconName = focused ? 'close-circle' : 'close-circle-outline';
          else if (route.name === 'Líder') iconName = focused ? 'shield-checkmark' : 'shield-checkmark-outline';
          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#3b82f6',
        tabBarInactiveTintColor: '#9ca3af',
        tabBarStyle: { backgroundColor: '#1f2937', borderTopColor: '#374151', height: 60, paddingBottom: 5 },
        headerShown: false
      })}
    >
      <Tab.Screen name="Minha Escala" component={HomeScreen} />
      <Tab.Screen name="Depto (Geral)" component={EscalaDepartamentoScreen} />
      <Tab.Screen name="Ausências" component={AusenciasScreen} />
      <Tab.Screen name="Líder" component={LiderStackNavigator} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer theme={DarkTheme}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="MainTabs" component={MainTabs} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
