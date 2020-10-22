//! Python bindings for the IR in Rust.
//! Because this operates across language boundaries, it makes use of `unsafe`
//! code.
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use std::ffi::c_void;

use calyx::ir;

unsafe impl Send for ComponentWrapper {}

/// Opaque wrapper struct for `ir::Component`.
/// It stores a `void*` pointer which **is not guaranteed** to be valid.
/// Functions that unwrap this component into a `Box` must call `raw_transform`
/// to make sure that the function does not run the drop method and frees
/// the component.
#[pyclass]
#[derive(Clone)]
struct ComponentWrapper {
    /// Raw pointer to the underlying `ir::Component`. Not guaranteed to
    /// be valid.
    comp: *mut c_void,
}

/// Transform a boxed ir::Component into a ComponentWrapper.
/// Leaks the underlying ir::Component so that it can be used by the
/// python library.
fn raw_transform(comp: Box<ir::Component>) -> ComponentWrapper {
    ComponentWrapper {
        comp: Box::into_raw(comp) as *mut c_void,
    }
}

/// Create a new component with the `name` and the inputs and outputs in
/// its signature.
/// Returns an opaque ComponentWrapper that can be used in other functions.
#[pyfunction]
fn new_component(
    name: &str,
    inputs: Vec<(&str, u64)>,
    outputs: Vec<(&str, u64)>,
) -> ComponentWrapper {
    let comp = Box::new(ir::Component::new(name, inputs, outputs));
    ComponentWrapper {
        comp: Box::into_raw(comp) as *mut c_void,
    }
}

/// Get the name of this Component.
#[pyfunction]
fn get_component_name(c: ComponentWrapper) -> String {
    unsafe {
        let comp_raw = c.comp as *mut ir::Component;
        let comp = Box::from_raw(comp_raw);
        let ret = comp.name.to_string();
        // Make sure that `comp` is not dropped.
        raw_transform(comp);
        ret
    }
}

/// Free the underlying ir::Component. All components must have this
/// method called on them to ensure that they don't leak.
#[pyfunction]
fn free_component(c: ComponentWrapper) -> () {
    unsafe {
        let comp_raw = c.comp as *mut ir::Component;
        Box::from_raw(comp_raw);
    }
}

/// The python module exposing the relevant functions.
#[pymodule]
fn libcalyx_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(new_component, m)?)?;
    m.add_function(wrap_pyfunction!(get_component_name, m)?)?;
    m.add_function(wrap_pyfunction!(free_component, m)?)?;

    Ok(())
}
