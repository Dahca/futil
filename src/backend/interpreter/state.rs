use crate::lang::ast;
use std::collections::HashMap;

/// Recursively stores a component's state
#[derive(Debug, Clone)]
pub enum State {
    /// Mapping from instance Ids to states for user-defined subcomponents
    Component(HashMap<ast::Id, State>),
    /// State for a primitive register component
    Register(Option<i64>),
}